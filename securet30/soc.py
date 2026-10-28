"""Run the Surface RT first-stage boot code on a Unicorn CPU against a model of the Tegra30 SoC.

The harness maps the image into DRAM, maps IRAM, and backs the peripheral aperture with a register model: registers
without a model read back what was last written; the live ones (PLL lock, power-gating, microsecond counter, UART
transmit as a console log, PMC reset reason, the L2 cache controller's ID and maintenance operations, the eMMC
controller in sdhci.py) let the code make progress. It runs the
AVP phase, then the A9 from the reset vector the AVP programmed, and translates through a page table it fills once
the stage enables the MMU.

Because the boot ROM is not run, the harness supplies what it leaves behind, from the BCT: the BCT copy in IRAM that
the Boot Information Table points to, and PLLM and the memory controller programmed from the selected SDRAM set.

It is an observation tool: it reports which path the code takes (visited blocks, cp15 accesses, console output,
accesses to hardware without a model, the accesses to chosen address ranges, and where it stops or faults).
"""
import collections
import os
import struct

from unicorn import (Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_PROT_ALL, UC_PROT_READ, UC_PROT_WRITE,
                     UC_HOOK_BLOCK, UC_HOOK_CODE, UC_HOOK_MEM_UNMAPPED, UC_ERR_INSN_INVALID,
                     UC_TLB_CPU, UC_CTL_TLB_FLUSH, UC_CTL_IO_WRITE, UcError)
from unicorn import arm_const as ac
from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_PC, UC_ARM_REG_LR, UC_CPU_ARM_CORTEX_A9

from .image import Image
from .sdhci import Sdhci

DRAM_BASE, DRAM_SIZE = 0x80000000, 0x80000000      # full 2 GiB of DRAM, so the 0-based alias resolves to real pages
IRAM_BASE, IRAM_SIZE = 0x40000000, 0x00040000      # on-chip RAM; the boot ROM leaves its hand-over table here
STACK_TOP = DRAM_BASE + 0x01ff0000                 # SP start for the flat (pre-MMU) phase; the stage sets its own
SENTINEL = 0xfffffff0                              # LR value whose execution ends a phase (no real return site)
BLOCK_TAIL = 512                                   # basic blocks kept for the trace tail; a full run enters millions
# The stage's 0-based stack lives just under 2 GiB (0x7fffxxxx), in the aperture between the peripherals (which end
# at USB, 0x7d00c000) and DRAM. Back it with real RAM so flat-phase pushes don't hit the MMIO sink; the peripheral
# aperture is the band below it.
LOWRAM_BASE, LOWRAM_SIZE = 0x7e000000, DRAM_BASE - 0x7e000000     # 0-based stack scratch
MMIO_BASE, MMIO_SIZE = IRAM_BASE + IRAM_SIZE, LOWRAM_BASE - (IRAM_BASE + IRAM_SIZE)   # peripheral aperture

# The stage enables the MMU with a page table the boot ROM would have filled; it leaves it empty here. _build_pt
# fills it (at the stage's own TTBR0) so Unicorn (UC_TLB_CPU) translates: everything from 0x40000000 up is identity
# (peripherals, the stack scratch, and DRAM), and the low 0-based range (< 0x40000000) aliases DRAM at 0x80000000 --
# that alias is what OpenSSL needs so a buffer written 0-based reads back through the identity view.
PT_SECTION = 0xc02          # L1 short-descriptor: 1 MiB section, AP = read/write all, non-cached, domain 0
TMRUS = 0x60005010          # free-running microsecond counter (read)
UART_BASES = (0x70006000, 0x70006040, 0x70006200, 0x70006300, 0x70006400)   # A, B, C, D, E; THR at +0, LSR at +0x14
ARM_REGS = [getattr(ac, 'UC_ARM_REG_R%d' % i) for i in range(13)] + [UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC]

# CP15 system registers, keyed (opc1, CRn, CRm, opc2). Unicorn's A9 core cannot decode the TrustZone ones, so the
# harness logs and skips every cp15/cp14 access; the names let the log read as the secure-world setup it is.
CP15_NAMES = {
    (0, 0, 0, 0): 'MIDR', (0, 0, 0, 5): 'MPIDR',
    (0, 1, 0, 0): 'SCTLR', (0, 1, 0, 1): 'ACTLR', (0, 1, 0, 2): 'CPACR',
    (0, 1, 1, 0): 'SCR', (0, 1, 1, 1): 'SDER', (0, 1, 1, 2): 'NSACR',
    (0, 2, 0, 0): 'TTBR0', (0, 2, 0, 1): 'TTBR1', (0, 2, 0, 2): 'TTBCR',
    (0, 3, 0, 0): 'DACR',
    (0, 12, 0, 0): 'VBAR', (0, 12, 0, 1): 'MVBAR', (0, 12, 1, 0): 'ISR',
    (4, 15, 0, 0): 'CBAR',          # A9 configuration base address (SCU/GIC)
}
APB_GP_HIDREV = 0x70000804      # chip id in bits [15:8]; 0x30 = Tegra30
SDMMC4_BASE, SDMMC4_SIZE = 0x78000600, 0x200    # eMMC host controller (SDHCI); modeled in sdhci.py
PG_UP_TAG = 0x60000000          # reads 0x55555555 for the CPU complex, 0xaaaaaaaa for the AVP (COP)
FLOW_HALT_COP = 0x60007004      # FLOW_CTLR_HALT_COP_EVENTS: FLOW_MODE that halts (STOP) or runs (NONE) the AVP
FLOW_MODE_STOP = 2 << 29
EVP_CPU_RESET = 0x6000f100      # EVP CPU reset vector: the A9 entry the AVP programs before halting
EVP_COP_RESET = 0x6000f200      # EVP COP reset vector: the AVP entry the A9 programs to restart it (the SPL)
PMC_BASE = 0x7000e400
PMC_PWRGATE_TOGGLE, PMC_PWRGATE_STATUS = 0x30, 0x38         # partition START | id -> toggles the id's status bit
PMC_CNTRL, PMC_CNTRL_MAIN_RST = 0x0, 1 << 4                 # MAIN_RST: system reset (ends the run)
PMC_SCRATCH0, PMC_SCRATCH0_RCM = 0x50, 1 << 1               # read by the boot ROM; RCM: enter USB recovery (APX)
PMC_RST_STATUS = 0x1b4                                      # reset reason, supplied by the harness
L2C_BASE = 0x50043000           # PL310 (L2C-310) L2 cache controller
L2C_READONLY = {0x000: 0x410000c7, 0x004: 0x1c400400}  # CACHE_ID, CACHE_TYPE, as read on a Surface RT
L2C_MAINT = {0x730, 0x77c, 0x7bc, 0x7fc}   # CACHE_SYNC, INV_WAY, CLEAN_WAY, CLEAN_INV_WAY: done at once, read 0
CAR_BASE = 0x60006000
PLL_LOCK = 1 << 27          # LOCK bit in each CAR PLL*_BASE register
PLL_BASES = {CAR_BASE + off for off in range(0x80, 0x100, 0x10)}            # PLLC/M/P/A/U/D/X base registers
UART_THR = {u for u in UART_BASES}
UART_LSR = {u + 0x14 for u in UART_BASES}

# Boot ROM hand-over. Tegra30 BCT layout: NVIDIA cbootimage, src/t30/nvboot_bct_t30.h and nvboot_sdram_param_t30.h.
_BCT = os.path.join(os.path.dirname(__file__), '..', 'data', 'spi-flash', 'leander-bct-decrypted.bin')
BIT_BCT_PTR = IRAM_BASE + 0x3c      # Boot Information Table: address of the BCT copy in IRAM
BCT_IRAM = IRAM_BASE + 0x20000      # where the harness puts that copy; the boot ROM's own placement is not known
BCT_SDRAM_PARAMS, BCT_SDRAM_SIZE = 0x148, 0x300     # sdram_params[4]
SDRAM_PLLM_DIVIDERS = 0xc           # pllm_input_divider (M), pllm_feedback_divider (N), pllm_post_divider (P)
SDRAM_MC_EMEM_CFG = 0x2a4
STRAPPING_OPT_A = 0x70000008        # RAM_CODE in bits [7:4]; its low two bits select the SDRAM set
MC_EMEM_CFG = 0x7000f050            # DRAM size in MiB
PLLM_BASE = CAR_BASE + 0x90
PLL_ENABLE = 1 << 30
# Reset values are not modelled (unwritten registers read 0); these stand in where code divides by a field:
# PLLD_BASE and PLLD2_BASE with DIVM 1, disabled.
RESET_STANDINS = {CAR_BASE + 0xd0: 1, CAR_BASE + 0x4b8: 1}


class Tegra:
    def __init__(self, image, *, trace=False, boot0=None, boot1=None, bct=None):
        """boot0/boot1: eMMC boot-area images (default the data/emmc dumps); bct: the decrypted BCT the boot ROM
        hands over (default leander's, matching the default image)."""
        self.m = image if isinstance(image, Image) else Image(image)
        self.uc = uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        uc.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A9)      # before any mapping: fixes MPIDR/CBAR and A9 cp15 decode
        uc.ctl_tlb_mode(UC_TLB_CPU)                     # walk the page table once the stage enables the MMU
        self.console = bytearray()      # bytes written to any UART transmit holding register
        self.blocks = collections.deque(maxlen=BLOCK_TAIL)  # (pc, size) of the last BLOCK_TAIL blocks (trace tail)
        self.nblocks = 0                # total basic blocks entered (self.blocks keeps only the tail)
        self.us = 0                     # microsecond counter handed out at TMRUS
        self.pmc = {}                   # PMC byte offset -> value (e.g. reset status); default 0
        self.mem = dict(RESET_STANDINS) # MMIO word store: last value written, read back by default
        self.unmodelled = {}            # ('r'/'w', word address) -> [count, first pc] of accesses the store served
        self.log_ranges = []            # (start, end) address ranges whose MMIO accesses go to access_log
        self.access_log = []            # [phase index, core, pc, 'r'/'w', address, size, value, model, repeats], in
                                        # order; consecutive identical accesses share one entry
        self.fault = None               # (kind, address) if the run stopped on a memory fault
        self.halted = False             # set when the AVP halts itself at the FLOW controller
        self.reset = None               # PMC_SCRATCH0 at the moment the code requested a system reset (MAIN_RST)
        self.mmu_on = False             # set when the stage turns the MMU on (page table filled by then)
        self.ttbr0 = 0x81ef8000         # L1 table base; refined from the stage's own TTBR0 write
        self.is_avp = True              # which core the model answers PG_UP_TAG as; A9 phase sets it False
        self.cpu_entry = None           # A9 reset vector the AVP programmed, captured at the halt
        self.start_avp = False          # set when the A9 releases the AVP to run (restart handoff)
        self.phases = []                # (label, first block index, end reason) per run phase
        self.icount = 0                 # approximate instructions executed (sum of block sizes / 4)
        self.cp15 = []                  # (pc, 'mcr'/'mrc', name, spec, value) of each cp15/cp14 access, in order
        self.sdhci = Sdhci(uc, boot0, boot1)    # eMMC host controller + card, backed by the boot-area images
        self.sd_log = self.sdhci.cmd_log
        self._stop = set()              # PCs at which to stop the run
        self._hooks = {}                # va -> callable(Tegra) invoked when execution reaches va
        self.uart_sink = None           # callable(byte) for each UART transmit byte, for live output
        self.heartbeat = None           # callable(Tegra) every heartbeat_every blocks, for a live status line
        self.heartbeat_every = 0

        uc.mem_map(DRAM_BASE, DRAM_SIZE, UC_PROT_ALL)
        uc.mem_map(LOWRAM_BASE, LOWRAM_SIZE, UC_PROT_ALL)
        uc.mem_map(IRAM_BASE, IRAM_SIZE, UC_PROT_READ | UC_PROT_WRITE)
        uc.mmio_map(MMIO_BASE, MMIO_SIZE, self._mmio_read, None, self._mmio_write, None)
        for _, sva, sz, raw in self.m.secs:
            uc.mem_write(sva, self.m.b[raw:raw + sz])
        with open(bct or _BCT, 'rb') as f:
            self._bootrom_handover(f.read())

        uc.hook_add(UC_HOOK_BLOCK, self._on_block)
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, self._on_unmapped)
        for site in self._ttbr0_sites():                # capture the L1 table base the stage programs
            uc.hook_add(UC_HOOK_CODE, self._watch_ttbr0, begin=site, end=site)
        for site in self._sctlr_sites():                # fill the table and note the MMU turning on
            uc.hook_add(UC_HOOK_CODE, self._enable_mmu, begin=site, end=site)
        if trace:
            uc.hook_add(UC_HOOK_CODE, self._on_code)
        self._trace = trace

    # -- peripheral model -------------------------------------------------
    # Each access is served by a model ('sdhci', 'uart', 'flow', 'pmc', 'pll', 'l2c', 'timer', 'id') or the 'store',
    # which has none: a read returns what was last written there.
    def _mmio_read(self, uc, offset, size, _):
        addr = MMIO_BASE + offset
        value, model = self._read(addr, size)
        self._account('r', addr, size, value, model)
        return value

    def _mmio_write(self, uc, offset, size, value, _):
        addr = MMIO_BASE + offset
        self._account('w', addr, size, value & 0xffffffff, self._write(uc, addr, size, value))

    def _account(self, kind, addr, size, value, model):
        if model == 'store':
            self._note_unmodelled(kind, addr)
        if any(lo <= addr < hi for lo, hi in self.log_ranges):
            entry = [len(self.phases), 'AVP' if self.is_avp else 'A9', self.uc.reg_read(UC_ARM_REG_PC), kind, addr,
                     size, value, model, 1]
            last = self.access_log[-1] if self.access_log else None
            if last and last[:-1] == entry[:-1]:      # a polling loop: count it instead of growing the log
                last[-1] += 1
            else:
                self.access_log.append(entry)

    def _read(self, addr, size):
        """One MMIO read -> (value, model)."""
        if SDMMC4_BASE <= addr < SDMMC4_BASE + SDMMC4_SIZE:
            return self.sdhci.read(addr - SDMMC4_BASE, size), 'sdhci'
        if addr == PG_UP_TAG:
            return (0xaaaaaaaa if self.is_avp else 0x55555555), 'id'
        if addr == APB_GP_HIDREV:
            return 0x3000, 'id'         # chip id 0x30 (Tegra30), revision fields zero
        if addr == TMRUS:
            self.us += 1
            return self.us & 0xffffffff, 'timer'
        if PMC_BASE <= addr < PMC_BASE + 0x400:
            off = addr - PMC_BASE
            return self.pmc.get(off, 0), ('pmc' if off in (PMC_PWRGATE_STATUS, PMC_RST_STATUS) else 'store')
        if addr in UART_LSR:                # TX holding + shift empty, so transmit loops exit
            return 0x60, 'uart'
        if addr - L2C_BASE in L2C_READONLY:
            return L2C_READONLY[addr - L2C_BASE], 'l2c'
        if addr - L2C_BASE in L2C_MAINT:
            return 0, 'l2c'
        val = self.mem.get(addr & ~3, 0)
        if (addr & ~3) in PLL_BASES:        # report the PLL as locked so clock init proceeds
            return val | PLL_LOCK, 'pll'
        return val, 'store'

    def _write(self, uc, addr, size, value):
        """Apply one MMIO write -> the model that took it."""
        if SDMMC4_BASE <= addr < SDMMC4_BASE + SDMMC4_SIZE:
            self.sdhci.write(addr - SDMMC4_BASE, size, value)
            return 'sdhci'
        if addr in UART_THR and size == 1:
            self.console.append(value & 0xff)
            if self.uart_sink:
                self.uart_sink(value & 0xff)
            return 'uart'
        if addr == FLOW_HALT_COP:
            self.mem[addr & ~3] = value & 0xffffffff
            if self.is_avp and value & FLOW_MODE_STOP and self.mem.get(EVP_CPU_RESET):
                self.cpu_entry = self.mem[EVP_CPU_RESET]     # AVP halts itself after programming the A9 vector
                self.halted = True
                uc.emu_stop()
            elif not self.is_avp and not value & FLOW_MODE_STOP and self.mem.get(EVP_COP_RESET):
                self.start_avp = True                        # the A9 released the AVP (FLOW_MODE_NONE) to restart
                uc.emu_stop()
            return 'flow'
        if PMC_BASE <= addr < PMC_BASE + 0x400:
            off = addr - PMC_BASE
            if off == PMC_CNTRL and value & PMC_CNTRL_MAIN_RST:
                self.reset = self.pmc.get(PMC_SCRATCH0, 0)
                uc.emu_stop()
                return 'pmc'
            model = 'store'
            if off == PMC_PWRGATE_TOGGLE and value & 0x100:        # START: flip the partition's status bit
                self.pmc[PMC_PWRGATE_STATUS] = self.pmc.get(PMC_PWRGATE_STATUS, 0) ^ (1 << (value & 0x1f))
                model = 'pmc'
            self.pmc[off] = value & 0xffffffff
            return model
        if addr - L2C_BASE in L2C_READONLY or addr - L2C_BASE in L2C_MAINT:
            return 'l2c'
        self.mem[addr & ~3] = value & 0xffffffff
        return 'pll' if (addr & ~3) in PLL_BASES else 'store'

    def _note_unmodelled(self, kind, addr):
        n = self.unmodelled.get((kind, addr & ~3))
        if n:
            n[0] += 1
        else:
            self.unmodelled[(kind, addr & ~3)] = [1, self.uc.reg_read(UC_ARM_REG_PC)]

    def _bootrom_handover(self, bct):
        """Leave what the boot ROM leaves for the next stage: the BCT copy in IRAM, which the Boot Information Table
        points to, and PLLM and the memory controller's DRAM size from the SDRAM set the RAM code selects."""
        self.uc.mem_write(BCT_IRAM, bct)
        self.uc.mem_write(BIT_BCT_PTR, struct.pack('<I', BCT_IRAM))
        sdram = BCT_SDRAM_PARAMS + ((self.mem.get(STRAPPING_OPT_A, 0) >> 4) & 3) * BCT_SDRAM_SIZE
        m, n, p = struct.unpack_from('<3I', bct, sdram + SDRAM_PLLM_DIVIDERS)
        self.mem[PLLM_BASE] = PLL_ENABLE | p << 20 | n << 8 | m
        self.mem[MC_EMEM_CFG] = struct.unpack_from('<I', bct, sdram + SDRAM_MC_EMEM_CFG)[0]

    # -- introspection ----------------------------------------------------
    def _on_block(self, uc, addr, size, _):
        self.blocks.append((addr, size))
        self.nblocks += 1
        self.icount += size // 4
        if self.heartbeat_every and self.nblocks % self.heartbeat_every == 0:
            self.heartbeat(self)
        if addr in self._hooks:
            self._hooks[addr](self)
        if addr in self._stop:
            uc.emu_stop()

    def _mcr_sites(self, encoding):
        """Addresses of every `mcr p15,0,Rt,...` matching encoding (Rt masked out) in the image."""
        return [sva + o for sva, d in self.m.code() for o in range(0, len(d) - 3, 4)
                if (struct.unpack_from('<I', d, o)[0] & 0xffff0fff) == encoding]

    def _sctlr_sites(self):
        return self._mcr_sites(0xee010f10)      # mcr p15,0,Rt,c1,c0,0 (SCTLR)

    def _ttbr0_sites(self):
        return self._mcr_sites(0xee020f10)      # mcr p15,0,Rt,c2,c0,0 (TTBR0)

    def _rt_value(self, addr):
        return self.reg(ARM_REGS[(int.from_bytes(self.uc.mem_read(addr, 4), 'little') >> 12) & 0xf])

    def _watch_ttbr0(self, uc, addr, size, _):
        self.ttbr0 = self._rt_value(addr) & 0xffffc000      # L1 table base (TTBCR N = 0)

    def _enable_mmu(self, uc, addr, size, _):
        if not self.mmu_on and self._rt_value(addr) & 1:    # SCTLR.M about to be set
            self._build_pt(self.ttbr0)
            uc.ctl(UC_CTL_TLB_FLUSH, UC_CTL_IO_WRITE)       # drop flat TLB entries cached while M was off
            uc.ctl_flush_tb()                               # and the flat translation blocks, so code re-walks
            self.mmu_on = True

    def _build_pt(self, base):
        """Fill the L1 table with 1 MiB sections: identity DRAM + peripherals, 0-based alias of DRAM elsewhere."""
        tbl = bytearray(0x4000)
        for i in range(4096):
            va = i << 20
            pa = va if va >= IRAM_BASE else (DRAM_BASE + va) & 0xffffffff   # identity >= 0x40000000, else DRAM alias
            struct.pack_into('<I', tbl, i * 4, pa | PT_SECTION)
        self.uc.mem_write(base, bytes(tbl))

    def _coproc(self, pc):
        """Log a cp15/cp14 access at pc that Unicorn would not decode, and return the next pc, or None."""
        w = int.from_bytes(self.uc.mem_read(pc, 4), 'little')
        if (w >> 24) & 0xf == 0xe and (w >> 4) & 1:             # mcr/mrc
            cpnum, read = (w >> 8) & 0xf, (w >> 20) & 1
            if cpnum not in (14, 15):
                return None
            spec = ((w >> 21) & 7, (w >> 16) & 0xf, w & 0xf, (w >> 5) & 7)    # opc1, CRn, CRm, opc2
            rt = (w >> 12) & 0xf
            name = CP15_NAMES.get(spec, 'p%d:%d:c%d:c%d:%d' % (cpnum, spec[0], spec[1], spec[2], spec[3]))
            if read:
                self.cp15.append((pc, 'mrc', name, spec, None))
                self.uc.reg_write(ARM_REGS[rt], 0)
            else:
                self.cp15.append((pc, 'mcr', name, spec, self.reg(ARM_REGS[rt])))
            return pc + 4
        if (w >> 25) & 7 == 0b110 and (w >> 8) & 0xf in (14, 15):    # ldc/stc/mcrr/mrrc
            self.cp15.append((pc, 'cp', 'p%d-long' % ((w >> 8) & 0xf), None, None))
            return pc + 4
        return None

    def _on_code(self, uc, addr, size, _):
        for insn in self.m.dis(addr, size):
            print('  %08x  %-8s %s' % (insn.address, insn.mnemonic, insn.op_str))

    def _on_unmapped(self, uc, access, addr, size, value, _):
        self.fault = ('write' if value else 'read', addr)
        return False                        # let the run stop with UC_ERR_*

    # -- control ----------------------------------------------------------
    def reg(self, r):
        return self.uc.reg_read(r)

    def dump_regs(self):
        """Core registers r0-r12, sp, lr, pc as one formatted line (read through Unicorn)."""
        names = ['R%d' % i for i in range(13)] + ['SP', 'LR', 'PC']
        return ' '.join('%s=%08x' % (n.lower(), self.reg(getattr(ac, 'UC_ARM_REG_' + n))) for n in names)

    def dump_stack(self, n=16, sp=None):
        """n words from sp (default the current SP) as (address, word...) lines, unmapped words shown as ???."""
        sp = self.reg(UC_ARM_REG_SP) if sp is None else sp
        out = []
        for i in range(0, n, 4):
            words = []
            for j in range(i, min(i + 4, n)):
                try:
                    words.append('%08x' % struct.unpack('<I', self.uc.mem_read(sp + 4 * j, 4))[0])
                except UcError:
                    words.append('????????')
            out.append('%08x: %s' % (sp + 4 * i, ' '.join(words)))
        return '\n'.join(out)

    def stop_at(self, *vas):
        self._stop.update(vas)

    def at(self, va, fn):
        """Call fn(self) when execution first reaches va (before the block runs)."""
        self._hooks[va] = fn

    def _phase(self, label, begin, count, timeout):
        at = self.nblocks
        self.uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        self.uc.reg_write(UC_ARM_REG_LR, SENTINEL)      # returning here ends the phase cleanly
        pc, reason = begin, 'stop'
        while True:
            rem = 0 if not count else max(1, count - self.icount)
            try:
                self.uc.emu_start(pc, SENTINEL, timeout=timeout, count=rem)
                if self.reset is not None:
                    reason = 'reset'
                elif self.halted:
                    reason = 'halted'
                elif self.reg(UC_ARM_REG_PC) == SENTINEL:
                    reason = 'returned'
                elif count and self.icount >= count:
                    reason = 'budget'
                break
            except UcError as e:
                if e.errno == UC_ERR_INSN_INVALID:
                    nxt = self._coproc(self.reg(UC_ARM_REG_PC))
                    if nxt is not None:
                        pc = nxt
                        continue
                reason = 'fault'
                if self.fault is None:
                    self.fault = (str(e), self.reg(UC_ARM_REG_PC))
                break
        self.phases.append((label, at, reason))

    def run(self, begin=None, *, count=0, timeout=0, handoff=True):
        """Run from the AVP entry (or begin), following each hand-off between the cores into a further phase:
        the AVP halting itself hands the A9 its reset vector, and the A9 releasing the AVP (the stub restarting it
        for the SPL) hands it back, so a full boot runs AVP (stage) -> A9 (stage, stub) -> AVP (SPL) -> A9 (U-Boot)."""
        self._phase('AVP' if begin is None else 'start',
                    self.m.base + self.m.entry if begin is None else begin, count, timeout)
        while handoff:
            if self.halted and self.cpu_entry is not None:
                self.halted = False
                self.is_avp = False
                self._phase('A9', self.cpu_entry, count, timeout)
            elif self.start_avp and self.mem.get(EVP_COP_RESET):
                self.start_avp = False
                self.is_avp = True
                self._phase('AVP', self.mem[EVP_COP_RESET], count, timeout)
            else:
                break
        return self
