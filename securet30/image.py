"""TE or PE image (UEFI modules of the Surface RT firmware) mapped at its image base, with ARM/Thumb disassemblers."""
import struct

import capstone

CODE_SECTIONS = ('PAGE', 'INIT')


class Image:
    def __init__(self, path):
        b = open(path, 'rb').read()
        self.b = b
        self.secs = []                                  # (name, address, size, file offset)
        te = 0
        if b[0x28:0x2c] == b'_FVH':                     # firmware volume: unwrap the TE module it carries
            te = b.find(b'VZ', struct.unpack_from('<H', b, 0x30)[0], 0x100)
        if b[te:te + 2] == b'VZ':
            _, nsec, _, strip, self.entry, _, self.base = struct.unpack_from('<HBBHIIQ', b, te + 2)
            delta = strip - 0x28                        # TE: the stripped headers are replaced by the 0x28-byte TE header
            for i in range(nsec):
                name, vsz, va, rsz, raw = struct.unpack_from('<8sIIII', b, te + 0x28 + 40 * i)[:5]
                self.secs.append((name.rstrip(b'\0').decode(), self.base + va, max(vsz, rsz), te + raw - delta))
            if te:                                      # map the whole volume in place: reset vector, headers, cert block
                load_base = self.base + strip - 0x28 - te
                self.secs.append(('_volume', load_base, len(b), 0))
                self.entry = load_base - self.base      # enter at the firmware-volume reset vector (blob offset 0)
        else:
            pe = struct.unpack_from('<I', b, 0x3c)[0]
            nsec = struct.unpack_from('<H', b, pe + 6)[0]
            opt = struct.unpack_from('<H', b, pe + 20)[0]
            self.entry = struct.unpack_from('<I', b, pe + 24 + 16)[0]
            self.base = struct.unpack_from('<I', b, pe + 24 + 28)[0]
            for i in range(nsec):
                name, vsz, va, rsz, raw = struct.unpack_from('<8sIIII', b, pe + 24 + opt + 40 * i)[:5]
                self.secs.append((name.rstrip(b'\0').decode(), self.base + va, max(vsz, rsz), raw))
        self.arm = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
        self.thumb = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
        self.arm.skipdata = self.thumb.skipdata = True

    def off(self, va):
        for _, sva, sz, raw in self.secs:
            if sva <= va < sva + sz:
                return raw + va - sva
        return None

    def read(self, va, n):
        o = self.off(va)
        return b'' if o is None else self.b[o:o + n]

    def u32(self, va):
        return struct.unpack('<I', self.read(va, 4))[0]

    def dis(self, va, n, thumb=False):
        return list((self.thumb if thumb else self.arm).disasm(self.read(va, n), va))

    def code(self):
        """(address, bytes) of each code section."""
        for name, sva, sz, raw in self.secs:
            if name.startswith('.text') or name in CODE_SECTIONS:
                yield sva, self.b[raw:raw + sz]

    def literal(self, insn, thumb=False):
        """Value loaded by a PC-relative LDR, or None."""
        if not (insn.mnemonic.startswith('ldr') and '[pc, #' in insn.op_str):
            return None
        pc = (insn.address + 4) & ~3 if thumb else insn.address + 8
        try:
            return self.u32(pc + int(insn.op_str.split('#')[1].rstrip(']'), 0))
        except (struct.error, ValueError):
            return None
