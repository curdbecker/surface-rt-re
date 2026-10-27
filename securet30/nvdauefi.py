"""The eMMC NVDAUEFI table and UEFIDATA block, read from a boot partition's bytes the way the first stage reads them.

Layouts and values come from securet30sec.h (through securet30sec_loader). Inconsistent tables raise ValueError.
"""
import struct

import securet30sec_loader as stage

D = stage.DEFINES
TABLE, ENTRY, UEFIDATA = (stage.LAYOUTS[n] for n in ('NVDAUEFI_TABLE', 'NVDAUEFI_ENTRY', 'UEFIDATA_HEADER'))
BOOT0, BOOT1 = D['NVDAUEFI_DEVICE_BOOT0'], D['NVDAUEFI_DEVICE_BOOT1']
TYPE_NAMES = {v: k[len('NVDAUEFI_TYPE_'):] for k, v in D.items() if k.startswith('NVDAUEFI_TYPE_')}
_FMT = {1: '<B', 2: '<H', 4: '<I', 8: '<Q'}


def get(buf, base, layout, name):
    """Value of the scalar field `name` of the struct `layout` at buf[base]."""
    f = layout.fields[name]
    return struct.unpack_from(_FMT[f.size], buf, base + f.offset)[0]


def put(buf, base, layout, name, value):
    """Store `value` in the scalar field `name` of the struct at buf[base]; return (offset, bytes) written."""
    f = layout.fields[name]
    data = struct.pack(_FMT[f.size], value)
    buf[base + f.offset:base + f.offset + f.size] = data
    return base + f.offset, data


def find_table(boot):
    """Offset of the NVDAUEFI table in a boot partition, scanning as the first stage does, or None."""
    magic = D['NVDAUEFI_MAGIC'].encode()
    for off in range(0, len(boot) - TABLE.size + 1, D['NVDAUEFI_TABLE_STEP']):
        if boot[off:off + len(magic)] == magic:
            return off
    return None


def entries(boot):
    """The table's entries as dicts (the NVDAUEFI_ENTRY fields, plus 'at': the entry's offset in boot); [] if none.

    The table must describe itself (its NVDAUEFI_TYPE_TABLE entry) as boot0 at the offset it was found at.
    """
    off = find_table(boot)
    if off is None:
        return []
    slots = TABLE.fields['entries']
    out = []
    for i in range(min(get(boot, off, TABLE, 'count'), slots.size // ENTRY.size)):
        at = off + slots.offset + i * ENTRY.size
        e = {k: get(boot, at, ENTRY, k) for k in ('type', 'device', 'offset', 'size', 'load_address')}
        e['at'] = at
        out.append(e)
    own = entry(out, D['NVDAUEFI_TYPE_TABLE'])
    if not own or (own['device'], own['offset']) != (BOOT0, off):
        raise ValueError('the NVDAUEFI table at %#x does not describe itself as boot0 %#x' % (off, off))
    return out


def entry(entries, type_):
    """The first entry of NVDAUEFI type `type_`, or None."""
    for e in entries:
        if e['type'] == type_:
            return e
    return None


def uefidata(boot, entries):
    """Offset in boot of the UEFIDATA block (its entry on boot0, carrying the UEFIDATA tag), or None."""
    e = entry(entries, D['NVDAUEFI_TYPE_UEFIDATA'])
    if not e or e['device'] != BOOT0:
        return None
    tag = UEFIDATA.fields['tag']
    at = e['offset']
    return at if boot[at + tag.offset:at + tag.offset + tag.size] == D['UEFIDATA_TAG'].encode() else None
