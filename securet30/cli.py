"""Command line for the Surface RT first-stage emulator.

    python -m securet30 run IMAGE [--begin VA] [--stop SYM|VA ...] [--timeout SEC] [--count N]
                                  [--reset N] [--trace] [--regs] [--stack N] [--live] [--mmio]
                                  [--boot0 FILE] [--boot1 FILE] [--bct FILE] [--uboot-map FILE]
                                  [--payload FILE] [--payload-offset OFF]

The run reports the UART console output, where it stopped (a stop address, a memory fault, the timeout, or the
instruction budget), and the tail of the basic-block trace. The run is unlimited unless bounded: --stop runs to a
loader symbol or address, --timeout bounds the wall clock, --count caps instructions. --reset sets PMC_RST_STATUS
(the boot ROM reset reason). --trace prints every instruction (slow). --regs and --stack dump the core registers
and stack at the stop, --stack with the code addresses found on it. --mmio lists the accesses to hardware without
a model. --boot0/--boot1 back the eMMC boot areas with other images (an installed U-Boot, say), --bct is the BCT
the boot ROM hands over, and --uboot-map (U-Boot's System.map) symbolizes U-Boot proper, relocated or not.
--payload injects a raw ARM binary into the unsigned UEFIDATA tail and runs it after verify; --live streams the
UART and a per-block status line.
"""
import bisect
import argparse
import struct
import sys

from unicorn.arm_const import (UC_ARM_REG_PC, UC_ARM_REG_SP,
                               UC_ARM_REG_R0, UC_ARM_REG_R1)

from .soc import Tegra


def _symbolizer(uboot=None):
    """pc -> 'name' or 'name+off' from U-Boot's map (if given) or the loader's tables (importable without IDA);
    '' if unknown or far off."""
    try:
        from securet30sec_loader import SYMBOLS
    except Exception:
        SYMBOLS = {}
    syms = sorted((ea, name) for name, ea in SYMBOLS.items())
    addrs = [ea for ea, _ in syms]

    def sym(pc):
        if uboot and uboot.link(pc) is not None:
            return 'u-boot:' + uboot.sym(pc)
        i = bisect.bisect_right(addrs, pc) - 1
        if i < 0:
            return ''
        ea, name = syms[i]
        off = pc - ea
        return name if off == 0 else ('%s+%#x' % (name, off) if off < 0x4000 else '')
    return sym


def _inject_payload(t, data, off):
    """Put a raw binary in the unsigned UEFIDATA tail on boot0 and point entry_offset at it (the hijack).

    The image and its signature are untouched, so Pkcs7Verify passes; only the unsigned block changes, as
    the OS could on eMMC. entry_offset is computed so load_address + entry_offset lands on the injected bytes.
    """
    from securet30sec_loader import DATA
    from . import nvdauefi
    copy = next(ea for ea, v in DATA.items() if v[0] == 'uefidata')   # where uefidata_read copies the block
    boot0 = bytearray(t.sdhci.card.part[1])
    block = nvdauefi.uefidata(boot0, nvdauefi.entries(boot0))
    if block is None:
        raise SystemExit('securet30: no UEFIDATA block on boot0')
    hdr = nvdauefi.UEFIDATA
    load = nvdauefi.get(boot0, block, hdr, 'load_address') & 0xffffffff
    if off + len(data) > hdr.size:
        raise SystemExit('securet30: payload past the %#x bytes uefidata_read copies' % hdr.size)
    boot0[block + off:block + off + len(data)] = data
    entry = (copy + off - load) & 0xffffffff
    nvdauefi.put(boot0, block, hdr, 'entry_offset', entry)
    t.sdhci.card.part[1] = bytes(boot0)
    print('payload        : %d bytes at UEFIDATA+%#x -> runtime %#x; entry_offset=%#x (verify unaffected)'
          % (len(data), off, copy + off, entry))


def _resolve(tokens):
    """Map --stop tokens (loader symbol names or hex addresses) to addresses."""
    names = {}
    try:
        from securet30sec_loader import SYMBOLS as names
    except Exception:
        pass
    return [names[tok] if tok in names else int(tok, 16) for tok in tokens]


def _live(t, sym):
    """UART flows like a terminal and a debugger-style status line stays pinned below it (every 1M blocks)."""
    tty = sys.stdout.isatty()
    status = ['']
    ubuf = ['']

    def emit(line):            # a finished UART line, printed above the status line
        if tty:
            sys.stdout.write('\r\x1b[K' + line + '\n\r\x1b[K' + status[0])
        else:
            sys.stdout.write(line + '\n')
        sys.stdout.flush()

    def sink(b):
        if b == 0x0a:
            emit(ubuf[0])
            ubuf[0] = ''
        elif b != 0x0d:
            ubuf[0] += chr(b) if (32 <= b < 127 or b == 9) else '.'

    def beat(t):
        pc = t.reg(UC_ARM_REG_PC)
        status[0] = '[%s] #%-10d pc=%08x %-22s sp=%08x r0=%08x r1=%08x uart=%dB' % (
            'AVP' if t.is_avp else 'A9 ', t.nblocks, pc, sym(pc),
            t.reg(UC_ARM_REG_SP), t.reg(UC_ARM_REG_R0), t.reg(UC_ARM_REG_R1), len(t.console))
        sys.stdout.write('\r\x1b[K' + status[0]) if tty else sys.stdout.write(status[0] + '\n')
        sys.stdout.flush()

    t.uart_sink, t.heartbeat, t.heartbeat_every = sink, beat, 1_000_000


def _add_run(sub):
    r = sub.add_parser('run', help='emulate the first stage', description='Emulate the Surface RT first stage.')
    r.add_argument('image')
    r.add_argument('--begin', type=lambda s: int(s, 16))
    r.add_argument('--count', type=int, help='instruction budget (unset = unlimited; bound with --stop/--timeout)')
    r.add_argument('--stop', nargs='+', default=[], metavar='SYM|VA',
                   help='run until a loader symbol (e.g. load_uefi, verify_ok, uefi_jump) or hex address is reached')
    r.add_argument('--timeout', type=float, default=0, metavar='SEC', help='wall-clock limit in seconds')
    r.add_argument('--reset', type=lambda s: int(s, 16), default=0)
    r.add_argument('--trace', action='store_true')
    r.add_argument('--regs', action='store_true', help='print the core registers at the stop')
    r.add_argument('--stack', type=int, nargs='?', const=16, default=0, metavar='N',
                   help='dump N stack words at the stop (default 16)')
    r.add_argument('--live', action='store_true', help='stream UART output and a status heartbeat as the run goes')
    r.add_argument('--mmio', action='store_true', help='list the accesses to hardware without a model')
    r.add_argument('--boot0', metavar='FILE', help='eMMC boot area 1 image (default data/emmc/boot0.bin)')
    r.add_argument('--boot1', metavar='FILE', help='eMMC boot area 2 image (default data/emmc/boot1.bin)')
    r.add_argument('--bct', metavar='FILE', help='decrypted BCT the boot ROM hands over (default leander\'s)')
    r.add_argument('--uboot-map', metavar='FILE', help='U-Boot System.map, to symbolize U-Boot proper')
    r.add_argument('--payload', metavar='FILE',
                   help='inject a raw ARM binary into the unsigned UEFIDATA tail and run it after verify')
    r.add_argument('--payload-offset', type=lambda s: int(s, 0), default=0x100, metavar='OFF',
                   help='offset into the UEFIDATA block for the payload (default 0x100)')
    r.set_defaults(func=_cmd_run)


def main(argv=None):
    ap = argparse.ArgumentParser(prog='securet30', description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    _add_run(sub)
    a = ap.parse_args(argv)
    a.func(a)


def _cmd_run(a):
    count = a.count or 0            # no default budget; the user bounds the run with --count/--stop/--timeout
    t = Tegra(a.image, trace=a.trace, boot0=a.boot0, boot1=a.boot1, bct=a.bct)
    t.pmc[0x1b4] = a.reset                       # PMC_RST_STATUS at 0x7000e5b4
    uboot = None
    if a.uboot_map:
        from .uboot import UBootSymbols
        uboot = UBootSymbols(a.uboot_map)
        uboot.attach(t)
    sym = _symbolizer(uboot)
    if a.payload:
        with open(a.payload, 'rb') as f:
            _inject_payload(t, f.read(), a.payload_offset)
    if a.live:
        _live(t, sym)
    if a.stop:
        t.stop_at(*_resolve(a.stop))
    t.run(a.begin, count=count, timeout=int(a.timeout * 1_000_000))

    if a.live and sys.stdout.isatty():
        sys.stdout.write('\r\x1b[K')             # drop the pinned status line before the summary
    print('blocks entered : %d' % t.nblocks)
    print('phases         : ' + ', '.join('%s@%d:%s' % p for p in t.phases))
    if t.cpu_entry is not None:
        print('A9 entry       : %#x' % t.cpu_entry)
    if t.fault:
        print('fault          : %s @ %#x' % t.fault)
    if t.reset is not None:
        print('system reset   : PMC_SCRATCH0 = %#x%s' % (t.reset, ' (boot ROM enters APX)' if t.reset & 2 else ''))
    pc = t.reg(UC_ARM_REG_PC)
    print('pc             : %#x %s' % (pc, sym(pc)))
    if uboot and uboot.reloc_off is not None:
        print('u-boot reloc   : %#x' % uboot.reloc_off)
    if t.cp15:
        print('--- cp15/cp14 accesses (secure-world setup) ---')
        for pc, op, name, spec, val in t.cp15:
            v = '' if val is None else ' = %#010x' % val
            print('  %#010x  %s %-6s%s' % (pc, op, name, v))
    if a.regs:
        print('registers      : ' + t.dump_regs())
    if a.stack:
        print('stack          :')
        print(t.dump_stack(a.stack))
        sp = t.reg(UC_ARM_REG_SP)
        words = struct.unpack('<%dI' % a.stack, t.uc.mem_read(sp, 4 * a.stack))
        print('code addresses on the stack (return-address candidates):')
        for i, w in enumerate(words):
            if sym(w):
                print('  sp+%#05x  %#010x %s' % (4 * i, w, sym(w)))
    if a.mmio:
        print('--- accesses to hardware without a model (served by the read-back store) ---')
        for (kind, addr), (n, first) in sorted(t.unmodelled.items(), key=lambda e: e[0][1]):
            print('  %s %#010x  x%-6d first at %#x %s' % (kind, addr, n, first, sym(first)))
    if t.console:
        print('--- UART console ---')
        print(t.console.decode('latin1'))
        print('--- end console ---')
    print('last blocks     :')
    for pc, sz in list(t.blocks)[-20:]:
        print('  %#010x (%d) %s' % (pc, sz, sym(pc)))


if __name__ == '__main__':
    main()
