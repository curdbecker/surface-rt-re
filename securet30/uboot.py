"""Symbols of the U-Boot proper an emulated boot enters, from its System.map, before and after relocation."""
import bisect

from unicorn.arm_const import UC_ARM_REG_R0


class UBootSymbols:
    def __init__(self, path):
        self.syms = {}
        with open(path) as f:
            for line in f:
                fields = line.split()
                if len(fields) >= 3:
                    self.syms.setdefault(fields[2], int(fields[0], 16))
        self.table = sorted((ea, name) for name, ea in self.syms.items())
        self.addrs = [ea for ea, _ in self.table]
        self.start, self.end = self.syms['__image_copy_start'], self.syms['__image_copy_end']
        self.reloc_off = None           # relocated minus link address, once U-Boot has called relocate_code

    def attach(self, t):
        """Note the relocation offset when the run reaches relocate_code(relocaddr)."""
        t.at(self.syms['relocate_code'], self._relocating)

    def _relocating(self, t):
        self.reloc_off = (t.reg(UC_ARM_REG_R0) - self.start) & 0xffffffff

    def link(self, pc):
        """pc as a link-time address, or None if it lies in neither copy of the image."""
        if self.start <= pc < self.end:
            return pc
        if self.reloc_off is not None and self.start <= (pc - self.reloc_off) & 0xffffffff < self.end:
            return (pc - self.reloc_off) & 0xffffffff
        return None

    def sym(self, pc):
        """'name' or 'name+off' for pc in either copy; '' outside U-Boot."""
        a = self.link(pc)
        if a is None:
            return ''
        ea, name = self.table[bisect.bisect_right(self.addrs, a) - 1]
        return name if a == ea else '%s+%#x' % (name, a - ea)
