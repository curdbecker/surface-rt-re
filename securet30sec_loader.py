"""
securet30sec_loader.py - IDA loader for the Surface RT first stage (SecureT30Sec), from the decrypted boot-flash
bootloader (firmware volume + NVDASPICERTIFICA block, e.g. data/spi-flash/leander-bootloader-decrypted.bin).

The boot ROM loads the blob to LOAD_BASE and the TE sections run in place (section address = LOAD_BASE + blob
offset), so the blob is mapped as one image, split into segments by its structure. The loader adds the .reloc
fixups, the Tegra30 blocks the stage addresses (sparse), the known functions, data and registers below, and the
types and enums of securet30sec.h (shared with the installer and the payloads; read_header gives its C view,
LAYOUTS the struct offsets); the reset vector is ARM and IDA follows the switches into Thumb. Findings behind the
tables: README.md. The tables are plain data, importable without IDA. Targets IDA 9.x.

OpenSSL (securet30sec_openssl.h/.json, from gen_securet30sec_openssl.py): the header is parsed at load time; after
auto-analysis identify() names OpenSSL functions and applies the header's prototypes. Run this file as a script to
repeat it on an open database. Evidence, all read with IDA's argument tracking:
  - ERR_put_error(lib, func, ...) call sites: (lib, func) names the reporting function (OpenSSL's *_err.c tables).
  - __FILE__/__LINE__ arguments of the allocation/assertion sinks: the enclosing source function. This build's
    sources are shifted by a few lines per file, so the offset is calibrated per file on its exact matches.
  - ASN1_ITEM structures, found by their name string at +0x18, and the d2i/i2d/new/free wrappers passing them.
A function is named only when its evidence agrees (an inlined static helper yields to the one declared function).
The loader is authoritative: it replaces any conflicting name and prints a line when it overrides a differing one.
"""
import collections
import json
import os
import re
import struct

try:
    import ida_bytes
    import ida_entry
    import ida_fixup
    import ida_funcs
    import ida_ida
    import ida_idp
    import ida_loader
    import ida_nalt
    import ida_name
    import ida_offset
    import ida_auto
    import ida_regfinder
    import ida_segment
    import ida_segregs
    import ida_typeinf
    import ida_ua
    import idautils
    import idc
except ImportError:                      # imported for its tables outside IDA
    pass

HERE = os.path.dirname(os.path.realpath(__file__))
OPENSSL_HEADER = os.path.join(HERE, 'securet30sec_openssl.h')
OPENSSL_DB = os.path.join(HERE, 'securet30sec_openssl.json')

LOAD_BASE = 0x80808000
FORMAT = 'Surface RT first stage (SecureT30Sec, decrypted bootloader)'
THUMB = (0x8080db98, 0x80848444)                # OpenSSL and its glue; the rest of .text is ARM

# Tegra30 address blocks the stage addresses: name -> (start, end).
TEGRA30_BLOCKS = {
    'IRAM': (0x40000000, 0x40040000), 'SCU': (0x50040000, 0x50040100), 'GIC': (0x50040100, 0x50042000),
    'L2C': (0x50043000, 0x50044000), 'PG': (0x60000000, 0x60001000), 'TMR': (0x60005000, 0x60005400),
    'CAR': (0x60006000, 0x60007000), 'FLOW': (0x60007000, 0x60008000), 'SB': (0x6000c200, 0x6000c300),
    'GPIO': (0x6000d000, 0x6000e000), 'EVP': (0x6000f000, 0x60010000), 'BSEA/VDE': (0x60010000, 0x60012000),
    'APB_MISC': (0x70000000, 0x70001000), 'PINMUX': (0x70003000, 0x70004000), 'UART': (0x70006000, 0x70006500),
    'I2C': (0x7000c000, 0x7000d200), 'SPI/SLINK': (0x7000d400, 0x7000dc00), 'PMC': (0x7000e400, 0x7000e800),
    'MC': (0x7000f000, 0x7000f400), 'EMC': (0x7000f400, 0x7000f800), 'FUSE': (0x7000f800, 0x7000fc00),
    'SE': (0x70012000, 0x70014000), 'SDMMC': (0x78000000, 0x78000800), 'USB': (0x7d000000, 0x7d00c000),
}

# DRAM the stage uses outside its image: name -> (start, end).
DRAM_REGIONS = {
    'ttb': (0x81ef8000, 0x81efc000),            # L1 translation table at the stage's TTBR0
}

SDHCI_REGS = [                                  # SD Host Controller standard register set: offset, name, width
    (0x00, 'SDMA_SYSADDR', 4), (0x04, 'BLOCK_SIZE', 2), (0x06, 'BLOCK_COUNT', 2), (0x08, 'ARGUMENT', 4),
    (0x0c, 'TRANSFER_MODE', 2), (0x0e, 'COMMAND', 2), (0x10, 'RESPONSE0', 4), (0x14, 'RESPONSE1', 4),
    (0x18, 'RESPONSE2', 4), (0x1c, 'RESPONSE3', 4), (0x20, 'BUFFER_DATA', 4), (0x24, 'PRESENT_STATE', 4),
    (0x28, 'HOST_CONTROL', 1), (0x29, 'POWER_CONTROL', 1), (0x2a, 'BLOCK_GAP_CONTROL', 1),
    (0x2b, 'WAKEUP_CONTROL', 1), (0x2c, 'CLOCK_CONTROL', 2), (0x2e, 'TIMEOUT_CONTROL', 1),
    (0x2f, 'SOFTWARE_RESET', 1), (0x30, 'INT_STATUS', 2), (0x32, 'ERR_INT_STATUS', 2), (0x34, 'INT_ENABLE', 2),
    (0x36, 'ERR_INT_ENABLE', 2), (0x38, 'SIGNAL_ENABLE', 2), (0x3a, 'ERR_SIGNAL_ENABLE', 2),
    (0x3c, 'AUTO_CMD_ERR_STATUS', 2), (0x3e, 'HOST_CONTROL2', 2), (0x40, 'CAPABILITIES', 4),
    (0x44, 'CAPABILITIES1', 4), (0x48, 'MAX_CURRENT', 4), (0xfe, 'HOST_VERSION', 2),
]
UART_REGS = [(0x00, 'THR_RBR', 1), (0x04, 'IER', 1), (0x08, 'IIR_FCR', 1), (0x0c, 'LCR', 1), (0x10, 'MCR', 1),
             (0x14, 'LSR', 1), (0x18, 'MSR', 1)]
UART_BASES = {'A': 0x70006000, 'B': 0x70006040, 'C': 0x70006200, 'D': 0x70006300, 'E': 0x70006400}
SDMMC4_BASE = 0x78000600

# Registers: address -> (name, width, comment).
REGISTERS = {
    0x60000000: ('PG_UP_TAG', 4, '0x55555555 on the CPU complex, 0xaaaaaaaa on the AVP (COP)'),
    0x60005008: ('TMR2_PTV', 4, None), 0x6000500c: ('TMR2_PCR', 4, None),
    0x60005010: ('TIMERUS_CNTR_1US', 4, 'free-running microsecond counter'),
    0x60005014: ('TIMERUS_USEC_CFG', 4, None),
    0x60005100: ('WDT0_CONFIG', 4, None), 0x60005104: ('WDT0_STATUS', 4, None),
    0x60005108: ('WDT0_COMMAND', 4, None), 0x6000510c: ('WDT0_UNLOCK_PATTERN', 4, '0xc45a unlocks'),
    0x60006080: ('CAR_PLLC_BASE', 4, None), 0x60006090: ('CAR_PLLM_BASE', 4, None),
    0x600060a0: ('CAR_PLLP_BASE', 4, None), 0x600060b0: ('CAR_PLLA_BASE', 4, None),
    0x600060c0: ('CAR_PLLU_BASE', 4, None), 0x600060d0: ('CAR_PLLD_BASE', 4, None),
    0x600060e0: ('CAR_PLLX_BASE', 4, None),
    0x60007004: ('FLOW_CTLR_HALT_COP_EVENTS', 4, 'the AVP halts itself here'),
    0x6000f100: ('EVP_CPU_RESET_VECTOR', 4, 'A9 reset vector, programmed by the AVP'),
    0x70000804: ('APB_MISC_GP_HIDREV', 4, 'chip id in bits 15:8 (0x30 = Tegra30)'),
    0x7000e430: ('PMC_PWRGATE_TOGGLE', 4, None), 0x7000e438: ('PMC_PWRGATE_STATUS', 4, None),
    0x7000e5b4: ('PMC_RST_STATUS', 4, 'reset reason, bits 2:0 (1 = watchdog)'),
}
REGISTERS.update({base + off: ('UART%s_%s' % (u, n), w, None)
                  for u, base in UART_BASES.items() for off, n, w in UART_REGS})
REGISTERS.update({SDMMC4_BASE + off: ('SDMMC4_' + n, w, None) for off, n, w in SDHCI_REGS})

# Functions: address -> (name, thumb, comment, prototype or None).
FUNCTIONS = {
    0x80808158: ('_ModuleEntryPoint', False, 'TE entry, reached from the reset vector; AVP and A9 both start '
                 'here and part at the PG_UP_TAG check', None),
    0x80808514: ('emmc_read', False, 'block reader: device 1/2 = boot0/boot1, 0 = user area; boot0 continues '
                 'into boot1', None),
    0x80808790: ('uefidata_read', False, 'reads the UEFIDATA block (via ctx.uefidata, ctx passed by value) and copies '
                 'its first 0x280 bytes to uefidata', 'EFI_STATUS uefidata_read(NVDAUEFI_CTX ctx);'),
    0x808088e8: ('nv_verify_image', False, 'NVIDIA verifier without OpenSSL (fixed format, 2048-bit RSA key '
                 'compare, SHA-256, RSA); no reference to it', None),
    0x80808afc: ('Pkcs7Verify', False, 'EDK2-style Pkcs7Verify around OpenSSL PKCS7_verify (flags 0); the signed '
                 'content is InData = load address, DataLength = image_size',
                 'u8 Pkcs7Verify(const u8 *P7Data, u32 P7Length, const u8 *TrustedCert, u32 CertLength, '
                 'const u8 *InData, u32 DataLength);'),
    0x80808dec: ('load_uefi', False, 'finds the NVDAUEFI table, reads UEFIDATA, image and signature, verifies; '
                 'a1/a2 are the system memory base and size (added to the memory map by setup_memory_map)',
                 'void load_uefi(u32 mem_base, u32 mem_size);'),
    0x8080a5f8: ('heap_alloc', False, 'allocator; context at heap_ctx, else heap_ctx_default', None),
    0x8080b67c: ('wdt_arm', False, 'arms WDT0 on timer 2: wdt index ignored (hardcoded); start=0 only disarms; '
                 'period in microseconds', 'void wdt_arm(u32 wdt, u32 start, u32 period_us);'),
    0x8080c1c8: ('memmove', False, None, 'void *memmove(void *dst, const void *src, unsigned int n);'),
    0x8084ad60: ('sd_send_cmd', False, 'SDHCI command issue (SDMMC4)', None),
    0x8084b27c: ('sd_read_blocks', False, 'SDHCI block read by SDMA', None),
    0x8084d578: ('nv_sha256', False, 'first of the SHA-256 routines used by nv_verify_image', None),
    0x8084d8c8: ('nv_rsa', False, 'RSA routine used by nv_verify_image', None),
    0x8084ffc0: ('memcpy', False, None, None),
    # load_uefi helpers: bring-up, NVDA block fetch, the verify arguments, then the pre-handoff teardown.
    0x8080b78c: ('mmio_read32', False, None, 'u32 mmio_read32(volatile u32 *reg);'),
    0x8080b794: ('mmio_write32', False, 'returns the value written', 'u32 mmio_write32(volatile u32 *reg, u32 value);'),
    0x8080b60c: ('reset_was_watchdog', False, 'PMC_RST_STATUS bits 2:0 == 1', None),
    0x808084e0: ('decide_use_backup', False, 'true iff use_backup_on_wdt_reset is set and reset_was_watchdog; result '
                 'stored in use_backup_copy', None),
    0x80808c78: ('pinmux_setup_sdmmc4', False, 'writes 0x2b to the eMMC pad controls (PINMUX 0x70003260..0x70003290)',
                 None),
    0x8080884c: ('find_nvdauefi_table', False, 'scans the boot areas in 16 KiB steps for the NVDAUEFI table and fills '
                 'nvdauefi_ctx via parse_nvdauefi_table', 'EFI_STATUS find_nvdauefi_table(NVDAUEFI_CTX *ctx);'),
    0x8084f5d8: ('parse_nvdauefi_table', False, 'validates the NVDAUEFI magic (CompareMem) and pivots each entry into '
                 'ctx by its type. Two on-disk layouts into the same ctx slots: candidate+8 == 1 selects the compact '
                 'one (count+0xc, entries 0x20, type+0x10, types 1..0xa); else the full one (count+0x2c, entries '
                 '0x30 = NVDAUEFI_ENTRY, types 1..0x18)',
                 'EFI_STATUS parse_nvdauefi_table(NVDAUEFI_CTX *ctx, void *candidate);'),
    0x8080bef4: ('CompareMem', False, 'EDK2 CompareMem/memcmp: returns 0 when equal; no-op (0) when dst==src or n==0',
                 'int CompareMem(const void *a, const void *b, unsigned int n);'),
    0x808086cc: ('read_image_block', False, 'reads uefidata.image_size bytes of ctx.image to the caller-supplied '
                 'load address; with use_backup_copy, uefidata.backup_image_size bytes of ctx.image_backup, if its '
                 'offset and size and both uefidata backup sizes are nonzero; ctx and uefidata are passed by value',
                 'EFI_STATUS read_image_block(NVDAUEFI_CTX ctx, UEFIDATA_HEADER uefidata, void *load_dest);'),
    0x808085c8: ('read_signature_block', False, 'reads ctx.signature (or ctx.signature_backup) NVDASPISIGNATURE block '
                 'and unwraps it: *out_P7Data = block+0x14 (DER), *out_P7Length = *(u32 *)(block+0x10)',
                 'EFI_STATUS read_signature_block(NVDAUEFI_CTX ctx, UEFIDATA_HEADER uefidata, u8 **out_P7Data, '
                 'u32 *out_P7Length);'),
    0x80808494: ('read_trusted_cert', False, 'CopyMem of trust_anchor_der into a fresh buffer -> TrustedCert, '
                 'CertLength', None),
    0x8084beac: ('emmc_select_partition', False, 'CMD6 SWITCH of EXT_CSD PARTITION_CONFIG (index 0xb3) boot-partition '
                 'access: 0 = user area, 1 = boot0, 2 = boot1; caches the selection at emmc_geometry+4',
                 'EFI_STATUS emmc_select_partition(u32 access);'),
    0x8084eac4: ('setup_memory_map', False, 'adds the (base, size) region to a descriptor list built from the '
                 'template at 0x8086b7a8, allocates a 16 KiB-aligned block, configures the PL310 L2 (0x50043000) '
                 '(inferred: memory-map / cache set-up before load)',
                 'EFI_STATUS setup_memory_map(u32 mem_base, u32 mem_size, u32 attr);'),
    0x8080bf1c: ('CopyMem', False, 'EDK2 CopyMem: returns dst; no-op when n==0 or dst==src, else memmove',
                 'void *CopyMem(void *dst, const void *src, unsigned int n);'),
    0x8080bf3c: ('memset16', False, None, 'void memset16(u16 *dst, unsigned int count, u16 value);'),
    0x8080bf54: ('memset32', False, None, 'void memset32(u32 *dst, unsigned int count, u32 value);'),
    0x8080b8b0: ('read_ccsidr', False, 'select the cache level (CSSELR), return CCSIDR', 'u32 read_ccsidr(u32 csselr);'),
    0x8080b9b0: ('dcache_line_invalidate', False, 'DCISW', 'void dcache_line_invalidate(u32 setway);'),
    0x8080b9c0: ('dcache_line_clean_invalidate', False, 'DCCISW', 'void dcache_line_clean_invalidate(u32 setway);'),
    0x8080b9d0: ('dcache_line_clean', False, 'DCCSW', 'void dcache_line_clean(u32 setway);'),
    0x8080bbfc: ('dcache_iterate_setway', False, 'apply the given per-line op across all sets/ways',
                 'void dcache_iterate_setway(void *line_op);'),
    0x8080bc3c: ('dcache_clean_invalidate_all', False, 'thunk: dcache_iterate_setway with DCCISW',
                 'void dcache_clean_invalidate_all(void);'),
    0x8080b9e0: ('icache_invalidate_all', False, 'ICIALLU', 'void icache_invalidate_all(void);'),
    0x8080b81c: ('tlb_bp_invalidate_all', False, 'TLBIALL + BPIALL', 'void tlb_bp_invalidate_all(void);'),
    0x8080ba58: ('dcache_disable', False, 'clear SCTLR.C', 'void dcache_disable(void);'),
    0x8080ba90: ('icache_disable', False, 'clear SCTLR.I', 'void icache_disable(void);'),
    0x8080ba14: ('mmu_disable', False, 'clear SCTLR.M, then TLBIALL + BPIALL', 'void mmu_disable(void);'),
    0x8080ebb0: ('ERR_put_error', True, 'every call passes file NULL, line 0 (OPENSSL_NO_ERR)', None),
    0x808176b8: ('CRYPTO_malloc', True, None, None),
    0x808169fc: ('CRYPTO_malloc_locked', True, None, None),
    0x80816b48: ('CRYPTO_realloc', True, None, None),
    0x80816c64: ('CRYPTO_realloc_clean', True, None, None),
    0x80816c28: ('CRYPTO_push_info_', True, None, None),
    0x8081669c: ('OpenSSLDie', True, None, None),
}

# OpenSSL sinks that receive __FILE__/__LINE__: name -> (file argument, line argument).
SINK_ARGS = {'CRYPTO_malloc': (1, 2), 'CRYPTO_malloc_locked': (1, 2), 'CRYPTO_realloc': (2, 3),
             'CRYPTO_realloc_clean': (3, 4), 'CRYPTO_push_info_': (1, 2), 'OpenSSLDie': (0, 1)}
SOURCE_ROOT = 'openssl-0.9.8l/'     # __FILE__ strings are build paths; the part after this is the source path
MAX_LINE_SHIFT = 40                 # calibration window for the per-file line offset
LINE_FUZZ = 4                       # a site within this many lines of a sink use still counts (patch hunks)
ASN1_ITEM_SNAME = 0x18              # offset of sname in ASN1_ITEM
ASN1_ITYPE_MAX = 6                  # ASN1_ITYPE_NDEF_SEQUENCE
WRAPPER_MAX = 0x40                  # largest function treated as an ASN.1 d2i/i2d/new/free wrapper
ITEM_FUNCS = {0: 'ASN1_item_new', 1: 'ASN1_item_free', 2: 'ASN1_item_i2d', 3: 'ASN1_item_d2i'}  # by ASN1_ITEM arg
WRAPPERS = {0: '%s_new', 1: '%s_free', 2: 'i2d_%s', 3: 'd2i_%s'}
MIN_ITEM_VOTES = 3                  # wrappers needed to name an ASN1_item_* function

# Code locations inside functions: address -> (name or None, comment).
LABELS = {
    0x80808000: ('reset', 'firmware-volume zero vector: the boot ROM enters the blob here'),
    0x8080816c: (None, 'PG_UP_TAG: 0x55 -> A9 path, else AVP path'),
    0x80808180: ('uefi_jump', 'enter the loaded UEFI image: r0 = load address + entry offset '
                 '(uefidata +0x40, +0x48)'),
    0x80808188: ('avp_path', None),
    0x808081a0: ('a9_path', 'A9: mode stacks, then SCTLR (MMU and D-cache off, I-cache on)'),
    0x80808214: (None, 'APB_MISC_GP_HIDREV chip id'),
    0x80808f10: ('verify_failed', 'Pkcs7Verify result != 1: b .'),
    0x80808f30: ('verify_ok', 'Pkcs7Verify result == 1: hardware set-up, then uefi_jump'),
    0x8080b9fc: (None, 'SCTLR.M = 1: MMU on'),
}

# Data: address -> (name, type, comment).
DATA = {
    0x808566f4: ('heap_ctx_default', 'HEAP_CONTEXT *', None),
    0x80856718: ('wdt_timeout_ms', 'unsigned int', 'WDT0 period load_uefi arms before Pkcs7Verify'),
    0x80856720: ('use_backup_on_wdt_reset', 'unsigned int', 'after a watchdog reset, use the boot0 copy '
                 '(NVDAUEFI types 0xd/0x10); when set, load_uefi also arms WDT0 (wdt_timeout_ms) before '
                 'Pkcs7Verify, so a hang there resets into it'),
    0x80875c78: ('emmc_geometry', 'EMMC_GEOMETRY', None),
    0x80875d08: ('use_backup_copy', 'u8', 'decide_use_backup result: use the boot0 backup NVDAUEFI entries'),
    0x80875d0c: ('heap_ctx', 'HEAP_CONTEXT *', 'active heap context; 0 -> heap_ctx_default'),
    0x80876590: ('nvdauefi_ctx', 'NVDAUEFI_CTX', 'filled by find_nvdauefi_table; args[0..3] + the table region the '
                 'block selectors take by value'),
    0x80876830: ('uefidata', 'UEFIDATA_HEADER', 'copy of the UEFIDATA block (unsigned), from uefidata_read'),
}

HEADER = os.path.join(HERE, 'securet30sec.h')
_DIRECTIVE = re.compile(r'#\s*(\w+)\s*(.*)')


def read_header(path, include_dirs=(HERE,)):
    """Read a header shared with the assembler the way C sees it (__ASSEMBLER__ undefined): (defines, declarations).

    Supports the subset the shared headers use: #include "file" (beside the including file, then in include_dirs),
    #define NAME [VALUE], #ifdef/#ifndef/#else/#endif, and comments. A value is an int, a "string", or the name of
    an earlier define.
    """
    defines, decls = {}, []

    def value(text):
        text = text.strip()
        if not text:
            return None
        if text.startswith('"'):
            return text[1:-1]
        if text in defines:
            return defines[text]
        return int(text, 0)

    def read(p):
        with open(p) as f:
            src = f.read()
        src = re.sub(r'/\*.*?\*/', lambda m: '\n' * m.group().count('\n'), src, flags=re.S)
        src = re.sub(r'//[^\n]*', '', src)
        active = [True]
        for line in src.splitlines():
            m = _DIRECTIVE.match(line.strip())
            if not m:
                if all(active):
                    decls.append(line)
                continue
            op, arg = m.groups()
            if op in ('ifdef', 'ifndef'):
                active.append((arg.split()[0] in defines) == (op == 'ifdef'))
            elif op == 'else':
                active[-1] = not active[-1]
            elif op == 'endif':
                active.pop()
            elif not all(active):
                continue
            elif op == 'define':
                name, _, rest = arg.partition(' ')
                defines[name] = value(rest)
            elif op == 'include':
                name = arg.strip()[1:-1]
                for d in (os.path.dirname(p),) + tuple(include_dirs):
                    if os.path.exists(os.path.join(d, name)):
                        read(os.path.join(d, name))
                        break
                else:
                    raise ValueError('%s: cannot find %s' % (p, name))
            else:
                raise ValueError('%s: unsupported directive #%s' % (p, op))

    read(path)
    return defines, '\n'.join(decls)


Field = collections.namedtuple('Field', 'offset size')
Struct = collections.namedtuple('Struct', 'size align fields')
_BASE_SIZES = {'char': 1, 'unsigned char': 1, 'short': 2, 'unsigned short': 2, 'int': 4, 'unsigned int': 4,
               'long long': 8, 'unsigned long long': 8}
_POINTER_SIZE = 4                   # 32-bit ARM


def struct_layouts(decls, defines):
    """name -> Struct(size, align, fields: name -> Field(offset, size)) for each struct in decls (natural alignment).

    Supports what the header declares: scalar and struct typedefs, struct fields of those types, pointers, and
    arrays sized by a number or a define.
    """
    types = {k: (v, v) for k, v in _BASE_SIZES.items()}            # type -> (size, alignment)
    layouts = {}
    for m in re.finditer(r'typedef\s+([^;{]+?)\s+(\w+)\s*;|struct\s+(\w+)\s*\{([^}]*)\}\s*;', decls):
        if m.group(2):
            types[m.group(2)] = types[' '.join(m.group(1).split())]
            continue
        name, body = m.group(3), m.group(4)
        offset, align, fields = 0, 1, {}
        for stmt in body.split(';'):
            stmt = ' '.join(stmt.split())
            if not stmt:
                continue
            f = re.match(r'(.*?)(\s*\*\s*|\s+)(\w+)(?:\s*\[\s*(\w+)\s*\])?$', stmt)
            type_, ptr, field, count = f.groups()
            size, al = (_POINTER_SIZE, _POINTER_SIZE) if '*' in ptr else types[type_]
            n = 1 if count is None else defines[count] if count in defines else int(count, 0)
            offset = -(-offset // al) * al
            fields[field] = Field(offset, size * n)
            offset += size * n
            align = max(align, al)
        size = -(-offset // align) * align
        types['struct ' + name] = (size, align)
        layouts[name] = Struct(size, align, fields)
    return layouts


DEFINES, TYPES = read_header(HEADER)
LAYOUTS = struct_layouts(TYPES, DEFINES)

# Sizes the stage's own code fixes, as a check on the header: it steps the table entries by 0x30, reads the table
# 0x400 bytes at a time, copies 0x280 bytes of UEFIDATA, and passes the 0x2a0-byte context by value.
for _name, _size in (('NVDAUEFI_ENTRY', 0x30), ('NVDAUEFI_TABLE', 0x400), ('UEFIDATA_HEADER', 0x280),
                     ('NVDAUEFI_CTX', 0x2a0)):
    if LAYOUTS[_name].size != _size:
        raise ValueError('%s: %s is %#x bytes, the first stage uses %#x' % (HEADER, _name, LAYOUTS[_name].size, _size))

ENUM_PREFIXES = ('NVDAUEFI_DEVICE_', 'NVDAUEFI_TYPE_')      # #define groups the database gets as enums


def enum_decls():
    """IDA enum declarations, one per ENUM_PREFIXES group of DEFINES."""
    return '\n'.join('enum %s { %s };' % (p[:-1], ', '.join('%s = %#x' % (k, v) for k, v in DEFINES.items()
                                                             if k.startswith(p)))
                     for p in ENUM_PREFIXES)


SYMBOLS = {v[0]: ea for ea, v in list(FUNCTIONS.items()) + list(LABELS.items()) if v[0]}   # name -> address


def function_defines():
    """Header text for assembly payloads: FN_<name> for each FUNCTIONS address (bit 0 set for Thumb code)."""
    lines = ['/* Generated from securet30sec_loader.FUNCTIONS by function_defines(). */',
             '#ifndef SECURET30SEC_FUNCTIONS_H', '#define SECURET30SEC_FUNCTIONS_H']
    lines += ['#define FN_%s %#x' % (name, ea | int(thumb)) for ea, (name, thumb, _, _) in sorted(FUNCTIONS.items())]
    lines.append('#endif')
    return '\n'.join(lines) + '\n'


def layout(blob):
    """Segments of the blob as (name, start offset, end offset, class), or None if it is not the bootloader."""
    if len(blob) < 0x100 or blob[0x28:0x2c] != b'_FVH':
        return None
    fv_len = struct.unpack_from('<Q', blob, 0x20)[0]
    fv_hdr = struct.unpack_from('<H', blob, 0x30)[0]
    te = blob.find(b'VZ', fv_hdr, fv_hdr + 0x40)
    if te < 0 or fv_len > len(blob):
        return None
    nsec, strip = blob[te + 4], struct.unpack_from('<H', blob, te + 6)[0]
    base = struct.unpack_from('<Q', blob, te + 0x10)[0]
    if base + strip - 0x28 != LOAD_BASE + te:
        return None
    secs = []
    for i in range(nsec):
        name, vsz, va, rsz = struct.unpack_from('<8sIII', blob, te + 0x28 + 40 * i)
        start = base + va - LOAD_BASE
        secs.append((name.rstrip(b'\0').decode(), start, start + max(vsz, rsz),
                     'CODE' if name.startswith(b'.text') else 'DATA'))
    segs = [('reset', 0, 0x10, 'CODE'), ('fv_header', 0x10, fv_hdr, 'DATA'), ('ffs_header', fv_hdr, te, 'DATA'),
            ('te_header', te, secs[0][1], 'DATA')] + secs + [('fv_rest', secs[-1][2], fv_len, 'DATA')]
    if blob[fv_len:fv_len + 16] == b'NVDASPICERTIFICA':
        segs.append(('cert_block', fv_len, len(blob), 'DATA'))
    return segs


def relocations(blob, segs):
    """Blob offsets of the 32-bit absolute relocations in .reloc."""
    rel = next(((s, e) for n, s, e, _ in segs if n == '.reloc'), None)
    out = []
    o = rel[0] if rel else 0
    while rel and o + 8 <= rel[1]:
        page, size = struct.unpack_from('<II', blob, o)
        if size < 8:
            break
        for i in range((size - 8) // 2):
            e = struct.unpack_from('<H', blob, o + 8 + 2 * i)[0]
            if e >> 12 == 3:                            # IMAGE_REL_BASED_HIGHLOW
                out.append(page + (e & 0xfff) - (LOAD_BASE - _image_base(blob)))
        o += size
    return out


def _image_base(blob):
    te = blob.find(b'VZ', 0x48)
    return struct.unpack_from('<Q', blob, te + 0x10)[0]


def accept_file(li, filename):
    li.seek(0)
    if layout(li.read(li.size())) is None:
        return 0
    return {'format': FORMAT, 'processor': 'arm'}


def _segment(start, end, name, sclass, data=None):
    s = ida_segment.segment_t()
    s.start_ea, s.end_ea, s.bitness = start, end, 1
    s.perm = ida_segment.SEGPERM_READ | ida_segment.SEGPERM_EXEC            # code is read-only: see the reloc loop
    if sclass != 'CODE':
        s.perm |= ida_segment.SEGPERM_WRITE
    flags = ida_segment.ADDSEG_NOSREG | ida_segment.ADDSEG_OR_DIE
    if data is None:
        flags |= ida_segment.ADDSEG_SPARSE
    ida_segment.add_segm_ex(s, name.replace('/', '_'), sclass, flags)
    if data is not None:
        ida_loader.mem2base(data, start, start + len(data))
    _mode(start, False)


def _mode(ea, thumb):
    ida_segregs.split_sreg_range(ea, ida_idp.str2reg('T'), 1 if thumb else 0, ida_segregs.SR_user)


def _owned(ea):
    """True if the loader may (over)write this address: it carries no user name (so any name is loader auto-generated).

    A user name is the agreed boundary: the loader marks every name it sets SN_AUTO (auto-generated), overwrites those
    freely on a re-run, and never touches an address a person has named.
    """
    return not ida_bytes.has_user_name(ida_bytes.get_flags(ea))


def _name(ea, name):
    """Set an auto-generated name, leaving any user name in place."""
    if not _owned(ea):
        return
    ida_name.set_name(ea, name, ida_name.SN_NOCHECK | ida_name.SN_NOWARN | ida_name.SN_FORCE | ida_name.SN_AUTO)


def _data(ea, width):
    {1: ida_bytes.create_byte, 2: ida_bytes.create_word, 4: ida_bytes.create_dword}[width](ea, width)


def load_file(li, neflags, fmt):
    ida_idp.set_processor_type('arm', ida_idp.SETPROC_LOADER)
    ida_ida.inf_set_app_bitness(32)
    ida_typeinf.set_compiler_id(ida_typeinf.COMP_GNU)
    li.seek(0)
    blob = li.read(li.size())
    segs = layout(blob)

    for name, s, e, sclass in segs:
        _segment(LOAD_BASE + s, LOAD_BASE + e, name, sclass, blob[s:e])
    for name, (s, e) in list(TEGRA30_BLOCKS.items()) + list(DRAM_REGIONS.items()):
        _segment(s, e, name, 'DATA' if name in DRAM_REGIONS or name == 'IRAM' else 'MMIO')

    _mode(THUMB[0], True)
    _mode(THUMB[1], False)

    code = [(s, e) for _, s, e, sclass in segs if sclass == 'CODE']     # blob-offset ranges of the code segments
    for off in relocations(blob, segs):
        ea = LOAD_BASE + off
        fd = ida_fixup.fixup_data_t(ida_fixup.FIXUP_OFF32)
        fd.off = struct.unpack_from('<I', blob, off)[0]
        fd.set(ea)
        if any(s <= off < e for s, e in code):      # leave literal pools in read-only code for IDA to present inline
            continue
        ida_bytes.create_dword(ea, 4)               # a relocated word in .data is an address, so mark it an offset
        ida_offset.op_plain_offset(ea, 0, 0)

    protos = apply_labels()

    cert = next((LOAD_BASE + s for n, s, e, _ in segs if n == 'cert_block'), None)
    if cert is not None and _owned(cert):
        idc.SetType(cert, 'NVDA_BLOCK')
        _name(cert, 'trust_anchor_block')
        length = struct.unpack_from('<I', blob, cert - LOAD_BASE + 16)[0]
        ida_bytes.create_byte(cert + 20, length)
        _name(cert + 20, 'trust_anchor_der')
        ida_bytes.set_cmt(cert + 20, 'DER certificate: Microsoft Surface for RT Firmware CA 2012', True)

    ida_entry.add_entry(LOAD_BASE, LOAD_BASE, 'reset', True)
    if protos:
        import __main__
        setattr(__main__, 'securet30sec_after_analysis', _after_analysis)     # outlives the loader module
        _after_analysis.hook()
    return 1


def _openssl_db():
    with open(OPENSSL_DB) as f:
        return json.load(f)


def _import_openssl():
    """Parse the OpenSSL header's declarations into the database; return its prototype map (empty if no header).

    Called from load_file and again from identify(), so a standalone re-run of the script re-imports the OpenSSL
    types and prototypes before it re-applies them instead of relying on what a previous run left behind.
    """
    if not os.path.exists(OPENSSL_HEADER):
        return {}
    errors = ida_typeinf.parse_decls(None, OPENSSL_HEADER, None, ida_typeinf.HTI_FIL)
    if errors:
        print('securet30sec_loader: %d errors parsing %s' % (errors, OPENSSL_HEADER))
    return _openssl_db()['prototypes']


def apply_labels():
    """(Re-)apply the type declarations and the register/label/data/function tables to the open database.

    Runs at load time and again on a standalone re-run of the script. Every write goes through _owned, so it
    refreshes the loader's own auto-generated symbols and leaves user names (names, types and comments) untouched.
    Returns the OpenSSL prototype map, for the caller to drive identify()/the analysis hook.
    """
    if ida_typeinf.parse_decls(None, TYPES + '\n' + enum_decls(), None, ida_typeinf.HTI_DCL) != 0:
        print('securet30sec_loader: errors in the type declarations')
    protos = _import_openssl()
    for ea, (name, width, cmt) in REGISTERS.items():
        _data(ea, width)
        _name(ea, name)
        if cmt and _owned(ea):
            ida_bytes.set_cmt(ea, cmt, True)
    for ea, (name, cmt) in LABELS.items():
        if name:
            _name(ea, name)
        if cmt and _owned(ea):
            ida_bytes.set_cmt(ea, cmt, False)
    for ea, (name, type_, cmt) in DATA.items():
        if not _owned(ea):
            continue
        idc.SetType(ea, type_)              # type first: a struct type renames to stru_<ea>, so set the name after it
        _name(ea, name)
        if cmt:
            ida_bytes.set_cmt(ea, cmt, True)
    for ea, (name, thumb, cmt, proto) in FUNCTIONS.items():
        if thumb != (THUMB[0] <= ea < THUMB[1]):
            print('securet30sec_loader: %s at %#x lies outside its mode range' % (name, ea))
        ida_auto.auto_make_proc(ea)
        _name(ea, name)
        if _owned(ea):
            if cmt:
                ida_bytes.set_cmt(ea, cmt, True)
            if proto or name in protos:
                idc.SetType(ea, proto or protos[name])
    return protos


def _reg(ea, n):
    """Value of R<n> at ea, or None."""
    return ida_regfinder.find_reg_value(ea, ida_idp.str2reg('R%d' % n))


def _arg(call, n):
    """Value of argument n at a call; arguments past R3 through IDA's argument addresses."""
    if n < 4:
        return _reg(call, n)
    addrs = ida_typeinf.get_arg_addrs(call)
    if not addrs or len(addrs) <= n or addrs[n] == idc.BADADDR:
        return None
    insn = ida_ua.insn_t()
    if ida_ua.decode_insn(insn, addrs[n]) and insn.Op1.type == ida_ua.o_reg:
        return ida_regfinder.find_reg_value(addrs[n], insn.Op1.reg)
    return None


def _callers(name):
    """(site, caller start) of every call or jump to the named function from another function."""
    target = ida_name.get_name_ea(idc.BADADDR, name)
    if target == idc.BADADDR:
        return
    for site in idautils.CodeRefsTo(target, False):
        f = ida_funcs.get_func(site)
        if f and f.start_ea != target:
            yield site, f.start_ea


def _source(ea):
    s = ida_bytes.get_strlit_contents(ea, -1, ida_nalt.STRTYPE_C) if ea else None
    s = s.decode('latin1') if s else ''
    return s.split(SOURCE_ROOT, 1)[1] if SOURCE_ROOT in s else None


def _identified(ea, name, note):
    """Name a function (auto-generated) from OpenSSL evidence; leave any user name in place, noting a disagreement."""
    if ida_bytes.has_user_name(ida_bytes.get_flags(ea)):
        current = ida_funcs.get_func_name(ea)
        if current != name:
            print('securet30sec_loader: %#x has user name %s, OpenSSL evidence says %s (%s)' % (ea, current, name, note))
        return False
    if not ida_name.set_name(ea, name, ida_name.SN_NOWARN | ida_name.SN_NOCHECK | ida_name.SN_AUTO):
        return False
    f = ida_funcs.get_func(ea)
    if f:
        ida_funcs.set_func_cmt(f, 'OpenSSL: ' + note, True)
    return True


def _source_votes(db, votes):
    """Add the ERR and __FILE__/__LINE__ evidence per caller to votes; return the unmatched site count."""
    for site, f in _callers('ERR_put_error'):
        name = db['err'].get(str(_reg(site, 0)), {}).get(str(_reg(site, 1)))
        if name:
            votes[f][re.sub(r'\W', '_', name)].append('ERR(%d,%d)' % (_reg(site, 0), _reg(site, 1)))
    sites = collections.defaultdict(list)
    for sink, (fa, la) in SINK_ARGS.items():
        for site, f in _callers(sink):
            path, line = _source(_arg(site, fa)), _arg(site, la)
            if path and line:
                sites[path].append((f, line, sink))
    unmatched = 0
    for path, found in sites.items():
        rows = db['lines'].get(path, [])
        exact = {(r[0], r[1]): r for r in rows}
        shift = max(range(MAX_LINE_SHIFT + 1), key=lambda o: sum((ln - o, s) in exact for _, ln, s in found))
        if not any((ln - shift, s) in exact for _, ln, s in found):
            unmatched += len(found)
            continue
        for f, line, sink in found:
            src = line - shift
            row = exact.get((src, sink)) or min(
                (r for r in rows if r[1] == sink and abs(r[0] - src) <= LINE_FUZZ),
                key=lambda r: abs(r[0] - src), default=None)
            if row:
                votes[f][row[2]].append('%s:%d' % (path, row[0]))
            else:
                unmatched += 1
    return unmatched


def _decide(votes, protos):
    """Name per function from its votes, one function per name (most evidence wins); count named, ambiguous."""
    choice, ambiguous = {}, 0
    for f, c in votes.items():
        names = list(c)
        declared = [n for n in names if n in protos]
        if len(names) > 1 and len(declared) == 1:
            names = declared
        if len(names) == 1:
            choice[f] = names[0]
        else:
            ambiguous += 1
            func = ida_funcs.get_func(f)
            if func:
                ida_funcs.set_func_cmt(func, 'OpenSSL candidates: ' + ', '.join(sorted(c)), True)
    owner = {}
    for f, n in choice.items():
        if n not in owner or len(votes[f][n]) > len(votes[owner[n]][n]):
            owner[n] = f
    named = 0
    for n, f in owner.items():
        evidence = votes[f][n]
        named += _identified(f, n, ', '.join(sorted(set(evidence))[:4]) + (' ...' if len(set(evidence)) > 4 else ''))
    return named, ambiguous


def _asn1_items(names):
    """Name and type the ASN1_ITEM structures whose sname string is a declared item name; name -> address."""
    wanted, refs = set(names), collections.defaultdict(set)
    for seg in ('.text', '.data'):
        s = ida_segment.get_segm_by_name(seg)
        data = ida_bytes.get_bytes(s.start_ea, s.end_ea - s.start_ea) if s else b''
        for m in re.finditer(rb'(?<=\0)([A-Za-z0-9_]+)\0', data):
            name = m.group(1).decode()
            if name in wanted:
                for ref in idautils.DataRefsTo(s.start_ea + m.start()):
                    item = ref - ASN1_ITEM_SNAME
                    if item % 4 == 0 and ida_bytes.get_byte(item) <= ASN1_ITYPE_MAX:
                        refs[name].add(item)
    items = {}
    for name, found in refs.items():
        if len(found) == 1:
            item = found.pop()
            _name(item, name + '_it')
            if _owned(item):
                idc.SetType(item, 'ASN1_ITEM')
            items[name] = item
    return items


def _asn1_wrappers(items, protos):
    """Name ASN1_item_new/free/i2d/d2i by the register their item is passed in, then the wrappers calling them."""
    votes, wrappers = collections.defaultdict(collections.Counter), []
    for name, item in items.items():
        for ref in idautils.DataRefsTo(item):
            f = ida_funcs.get_func(ref)
            if not f or f.end_ea - f.start_ea > WRAPPER_MAX:
                continue
            hits = [(t, k) for h in idautils.FuncItems(f.start_ea) for t in idautils.CodeRefsFrom(h, False)
                    if t != f.start_ea and ida_funcs.get_func(t) and ida_funcs.get_func(t).start_ea == t
                    for k in ITEM_FUNCS if _reg(h, k) == item]
            if len(hits) == 1:
                wrappers.append((f.start_ea, name) + hits[0])
                votes[hits[0][1]][hits[0][0]] += 1
    callee = {}
    for k, c in votes.items():
        t, n = c.most_common(1)[0]
        if n >= MIN_ITEM_VOTES and _identified(t, ITEM_FUNCS[k], '%d wrappers pass the item in R%d' % (n, k)):
            callee[k] = t
    named = 0
    for f, name, t, k in wrappers:
        w = WRAPPERS[k] % name
        if callee.get(k) == t and w in protos:
            named += _identified(f, w, 'passes %s_it to %s' % (name, ITEM_FUNCS[k]))
    return named


def _apply_prototypes(protos):
    typed = 0
    for ea in idautils.Functions():
        name = ida_funcs.get_func_name(ea)
        if name in protos and _owned(ea):      # overwrite the loader's own types; leave user-named functions alone
            typed += bool(idc.SetType(ea, protos[name]))
    return typed


def identify():
    """Name OpenSSL functions from the database's evidence and apply the header's prototypes."""
    _import_openssl()               # (re-)import the header so a re-run restores the OpenSSL types before applying them
    db = _openssl_db()
    protos = db['prototypes']
    votes = collections.defaultdict(lambda: collections.defaultdict(list))
    unmatched = _source_votes(db, votes)
    named, ambiguous = _decide(votes, protos)
    items = _asn1_items(db['asn1_items'])
    wrapped = _asn1_wrappers(items, protos)
    typed = _apply_prototypes(protos)
    print('securet30sec_loader: named %d functions from ERR/__FILE__ evidence (%d ambiguous, %d sites unmatched), '
          '%d ASN1_ITEMs, %d ASN.1 wrappers; applied %d prototypes' % (
              named, ambiguous, unmatched, len(items), wrapped, typed))


class _AfterAnalysis(ida_idp.IDB_Hooks if 'ida_idp' in globals() else object):
    def auto_empty_finally(self):
        self.unhook()
        identify()


_after_analysis = _AfterAnalysis()

if __name__ == '__main__':             # re-run on an open database: re-apply the tables, then the OpenSSL evidence
    apply_labels()
    identify()
