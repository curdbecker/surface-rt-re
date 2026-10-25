"""SDHCI host controller and eMMC card model, as far as the Surface RT first stage drives them.

Standard SDHCI register semantics after QEMU's hw/sd (sd.c, sdhci.c): a 32-bit write to reg 0x0c issues a command
(index bits[29:24], response type bits[17:16], data present bit 21, transfer mode low 16) with the argument from reg
0x08 and block size/count from reg 0x04/0x06; responses land in 0x10-0x1c, PIO data at the buffer data port 0x20,
SDMA copies to the System Address in reg 0x00. Only what the stage exercises is implemented.

Backing store: boot area 1 = boot0.bin, boot area 2 = boot1.bin; the user area is not dumped and reads as zeroes.
"""
import os
import struct

CAPS = 0x07803000               # 3.3/3.0/1.8 V, high speed, 48 MHz base clock, 512-byte max block
TRAN_STATUS = 0x00000900        # card status: READY_FOR_DATA, current state = 4 (tran)
BOOT_SIZE = 0x200000            # 2 MiB per boot area (BOOT_SIZE_MULT = 16)

_EMMC = os.path.join(os.path.dirname(__file__), '..', 'data', 'emmc')


class EmmcCard:
    """eMMC card command state machine. command() returns (response, pio_bytes); DMA reads are served by Sdhci."""
    def __init__(self, boot0, boot1):
        self.part = {1: boot0, 2: boot1}        # access value -> boot-area bytes; 0 (user) -> zeroes
        self.access = 0                         # EXT_CSD PARTITION_CONFIG[2:0], set by CMD6
        self.rca = 0
        self.ext_csd = self._ext_csd()
        self.cid = self._r2(0x15, 0x01)         # plausible CID (MID 0x15 = Samsung-like)
        self.csd = self._csd()

    def _ext_csd(self):
        e = bytearray(512)
        e[179] = 0                              # PARTITION_CONFIG
        e[196] = 0x03                           # DEVICE_TYPE: HS 26/52 MHz
        e[192] = 6                              # EXT_CSD_REV (v4.5)
        e[226] = BOOT_SIZE // 0x20000           # BOOT_SIZE_MULT = 16 (x 128 KiB)
        struct.pack_into('<I', e, 212, 0x07460000)      # SEC_COUNT (user area; MCG8GA = 58.2 GiB, from dmesg)
        return e

    def _csd(self):
        c = bytearray(16)                       # device size = (C_SIZE+1) << (C_SIZE_MULT+2) blocks of READ_BL_LEN
        c[0] = (1 << 6) | (4 << 2)              # CSD_STRUCTURE=1, SPEC_VERS=4
        c[5] = 0x09                             # READ_BL_LEN = 9 (512), bits[83:80]
        c[6] |= 0x03                            # C_SIZE[11:10] = 3  -> C_SIZE = 0xFFF
        c[7] = 0xFF                             # C_SIZE[9:2]
        c[8] |= 0xC0                            # C_SIZE[1:0]
        c[9] |= 0x03                            # C_SIZE_MULT[2:1] = 3 -> C_SIZE_MULT = 7 (0x200000-block capacity)
        c[10] |= 0x80                           # C_SIZE_MULT[0]
        c[15] = 0x01                            # CRC/stop placeholder (dropped by SDHCI)
        return bytes(c)

    @staticmethod
    def _r2(mid, crc):
        b = bytearray(16)
        b[0] = mid
        b[15] = crc
        return bytes(b)

    def command(self, idx, arg):
        if idx == 0:                            # GO_IDLE
            return None, None
        if idx == 1:                            # SEND_OP_COND -> OCR, ready + sector addressing
            return 0xC0FF8080, None
        if idx == 2:                            # ALL_SEND_CID
            return self.cid, None
        if idx == 3:                            # SET_RELATIVE_ADDR (host assigns RCA)
            self.rca = arg >> 16
            return TRAN_STATUS, None
        if idx == 9:                            # SEND_CSD
            return self.csd, None
        if idx == 8:                            # SEND_EXT_CSD (PIO data)
            return TRAN_STATUS, bytes(self.ext_csd)
        if idx == 6:                            # SWITCH: write one EXT_CSD byte
            access, index, value = (arg >> 24) & 3, (arg >> 16) & 0xff, (arg >> 8) & 0xff
            if access == 3 and index < 512:
                self.ext_csd[index] = value
                if index == 179:
                    self.access = value & 7
            return TRAN_STATUS, None
        return TRAN_STATUS, None                # 7 select, 13 status, 16 set_blocklen, 12 stop, reads: R1

    def blocks(self, lba, n):
        """n blocks of 512 bytes from the active partition at sector lba, zero-filled past the dump."""
        data = self.part.get(self.access)
        out = bytearray(n * 512)
        if data is not None:
            src = data[lba * 512: lba * 512 + n * 512]
            out[:len(src)] = src
        return bytes(out)


class Sdhci:
    """SDHCI controller over the SDMMC4 register window; serves PIO and SDMA from an EmmcCard."""
    def __init__(self, uc, boot0_path=None, boot1_path=None):
        self.uc = uc
        b0 = open(boot0_path or os.path.join(_EMMC, 'boot0.bin'), 'rb').read()
        b1 = open(boot1_path or os.path.join(_EMMC, 'boot1.bin'), 'rb').read()
        self.card = EmmcCard(b0, b1)
        self.regs = {}
        self.pio = b''
        self.pio_i = 0
        self.cmd_log = []               # (command index, argument)
        self.reads = []                 # (partition access, lba, block count) of every data read served

    def read(self, off, size):
        if off == 0x24:                 # Present State: card inserted; buffer-read-enable while PIO data remains
            return (1 << 16) | (0x400 if self.pio_i < len(self.pio) else 0)
        if off == 0x40:
            return CAPS
        if off == 0x44:
            return 0
        if off == 0x20:                 # Buffer Data Port (PIO)
            v = struct.unpack_from('<I', (self.pio + b'\0\0\0\0'), self.pio_i)[0]
            self.pio_i += 4
            return v
        return self.regs.get(off, 0)

    def write(self, off, size, value):
        value &= 0xffffffff
        if off == 0x2c:                 # Clock/Reset: reset bits (24-26) self-clear; clock-stable follows enable
            value &= ~0x07000000
            if value & 1:
                value |= 2
        if off == 0x30:                 # Normal/Error Interrupt Status: write-1-to-clear
            self.regs[0x30] = self.regs.get(0x30, 0) & ~value
            return
        self.regs[off] = value
        if off == 0x0c:
            self._issue(value)

    def _issue(self, v):
        idx, rtype, data, tm = (v >> 24) & 0x3f, (v >> 16) & 3, (v >> 21) & 1, v & 0xffff
        arg = self.regs.get(0x08, 0)
        self.cmd_log.append((idx, arg))
        resp, pio = self.card.command(idx, arg)
        if rtype == 1:                                  # R2: 136-bit, QEMU rspreg mapping (CRC byte dropped)
            r = resp
            self.regs[0x10] = struct.unpack('>I', r[11:15])[0]
            self.regs[0x14] = struct.unpack('>I', r[7:11])[0]
            self.regs[0x18] = struct.unpack('>I', r[3:7])[0]
            self.regs[0x1c] = (r[0] << 16) | (r[1] << 8) | r[2]
        elif rtype in (2, 3) and resp is not None:      # R1/R3/R6: 32-bit payload
            self.regs[0x10] = resp & 0xffffffff
        status = 0x1                                    # Command Complete
        if data and (tm & 0x10):                        # read
            if tm & 0x01:                               # SDMA: copy blocks into guest memory at reg 0x00
                n = max(1, (self.regs.get(0x04, 0) >> 16) & 0xffff)
                self.reads.append((self.card.access, arg, n))
                self.uc.mem_write(self.regs.get(0x00, 0), self.card.blocks(arg, n))
                status |= 0x2                           # Transfer Complete
            else:                                       # PIO (EXT_CSD)
                self.pio, self.pio_i = pio or b'', 0
                status |= 0x20                          # Buffer Read Ready
        self.regs[0x30] = self.regs.get(0x30, 0) | status
