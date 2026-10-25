"""Generate the OpenSSL knowledge the SecureT30Sec loader uses: a preprocessed header and an identification table.

    uv run tools/surface-rt/gen_securet30sec_openssl.py --tarball openssl-0.9.8l.tar.gz --edk2 EDK2_REPO

Builds the first stage's OpenSSL environment from the OpenSSL 0.9.8l release tarball and an edk2 git checkout
(CryptoPkg at --rev, the last commit with 0.9.8l): applies EDKII_openssl-0.9.8l.patch, lays out include/openssl as
CryptoPkg's Install.sh does, and preprocesses OpenSSL's and BaseCryptLib's public headers with OpensslLib.inf's
flags for a 32-bit GCC build. Writes next to this script:
  securet30sec_openssl.h     the declarations, for IDA's parser
  securet30sec_openssl.json  lines:  source file -> [line, sink, function, static] for every sink-macro use
                                     (line = the macro's last line, which is what __LINE__ gives)
                             err:    ERR_LIB value -> function code -> function name (from the *_err.c tables)
                             asn1_items: names X of the declared `extern const ASN1_ITEM X_it`
                             prototypes: function name -> its declaration in the header
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import tarfile
import tempfile

import clang.cindex as ci

TARBALL_SHA256 = 'ecd054e9eed2e9c1620ba15257e6fc4d882c9a4aea663d23b769e2138de8c91a'
EDK2_REV = '5359174326^'
OPENSSL_FLAGS = ('-DOPENSSL_SYSNAME_UWIN -DOPENSSL_SYS_UEFI -DL_ENDIAN -D_CRT_SECURE_NO_DEPRECATE '
                 '-D_CRT_NONSTDC_NO_DEPRECATE -DOPENSSL_NO_CAMELLIA -DOPENSSL_NO_SEED -DOPENSSL_NO_RC5 '
                 '-DOPENSSL_NO_MDC2 -DOPENSSL_NO_SOCK -DOPENSSL_NO_CMS -DOPENSSL_NO_JPAKE -DOPENSSL_NO_CAPIENG '
                 '-DOPENSSL_NO_ERR -DOPENSSL_NO_KRB5 -DOPENSSL_NO_DYNAMIC_ENGINE -DGETPID_IS_MEANINGLESS '
                 '-DOPENSSL_NO_STDIO -DOPENSSL_NO_FP_API -DOPENSSL_NO_DGRAM -DOPENSSL_NO_ASM '
                 '-DOPENSSL_SMALL_FOOTPRINT -DOPENSSL_NO_SHA0 -DOPENSSL_NO_SHA512 -DOPENSSL_NO_LHASH '
                 '-DOPENSSL_NO_HW -DOPENSSL_NO_OCSP -DOPENSSL_NO_LOCKING -DOPENSSL_NO_DEPRECATED '
                 '-U_WIN32 -U_WIN64 -DTHIRTY_TWO_BIT').split()
# Extensions IDA's parser does not take; the declarations stay the same without them.
IDA_DEFINES = ['-D__attribute__(x)=', '-D__extension__=', '-D__inline__=', '-D__inline=', '-D__restrict=',
               '-D__builtin_va_list=char *', '-D__asm__(x)=']
SINKS = {                                      # macro -> sink function it expands to
    'OPENSSL_malloc': 'CRYPTO_malloc', 'OPENSSL_malloc_locked': 'CRYPTO_malloc_locked',
    'OPENSSL_realloc': 'CRYPTO_realloc', 'OPENSSL_realloc_clean': 'CRYPTO_realloc_clean',
    'CRYPTO_push_info': 'CRYPTO_push_info_', 'OPENSSL_assert': 'OpenSSLDie',
}
HERE = os.path.dirname(os.path.abspath(__file__))


def sh(*cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw).stdout


def unpack(tarball, edk2, rev, root):
    if hashlib.sha256(open(tarball, 'rb').read()).hexdigest() != TARBALL_SHA256:
        raise SystemExit('tarball does not match the OpenSSL 0.9.8l release')
    archive = subprocess.run(['git', '-C', edk2, 'archive', rev, 'CryptoPkg', 'MdePkg'], check=True,
                             capture_output=True).stdout
    with tempfile.TemporaryFile() as f:
        f.write(archive)
        f.seek(0)
        tarfile.open(fileobj=f).extractall(root, filter='data')
    lib = os.path.join(root, 'CryptoPkg', 'Library', 'OpensslLib')
    tarfile.open(tarball).extractall(lib, filter='data')
    src = os.path.join(lib, 'openssl-0.9.8l')
    sh('patch', '-p0', '-i', os.path.join(lib, 'EDKII_openssl-0.9.8l.patch'), cwd=src)
    sh('sh', 'Install.sh', cwd=lib)
    return src


def include_args(root, src):
    inc = [os.path.join(root, 'CryptoPkg', 'Include'), os.path.join(root, 'MdePkg', 'Include'),
           os.path.join(root, 'MdePkg', 'Include', 'Arm'), src, os.path.join(src, 'crypto')]
    return ['-I' + d for d in inc]


def public_headers(root):
    names = sorted(os.listdir(os.path.join(root, 'CryptoPkg', 'Include', 'openssl')))
    return [n for n in names if n.endswith('.h')]


def preprocess(root, src, extra):
    master = os.path.join(root, 'master.h')
    with open(master, 'w') as f:
        f.write('#include <Base.h>\n#include <Library/BaseCryptLib.h>\n')
        f.writelines('#include <openssl/%s>\n' % n for n in public_headers(root))
    args = ['arm-none-eabi-gcc', '-E', '-nostdinc', '-mthumb', '-march=armv7-a', '-fno-short-enums']
    return sh(*args, *extra, *OPENSSL_FLAGS, *include_args(root, src), master)


def defines(root, src):
    out = preprocess(root, src, ['-dM'])
    vals = {}
    for m in re.finditer(r'^#define (\w+) (\(?-?(?:0x[0-9a-fA-F]+|\d+)L?\)?)$', out, re.M):
        vals[m.group(1)] = int(m.group(2).strip('()').rstrip('L'), 0)
    return vals


def err_table(src, vals):
    table = {}
    for dirpath, _, files in os.walk(os.path.join(src, 'crypto')):
        for name in files:
            if not name.endswith('_err.c'):
                continue
            text = open(os.path.join(dirpath, name), errors='replace').read()
            lib = re.search(r'#define\s+ERR_FUNC\(func\)\s+ERR_PACK\((ERR_LIB_\w+)\s*,', text)
            if not lib or lib.group(1) not in vals:
                continue
            funcs = table.setdefault(str(vals[lib.group(1)]), {})
            for m in re.finditer(r'\{ERR_FUNC\((\w+)\)\s*,\s*"([^"]*)"\}', text):
                if m.group(1) in vals:
                    funcs[str(vals[m.group(1)])] = m.group(2)
    return table


def _macro_end(lines, i, col):
    """Line index of the closing parenthesis of the macro call starting at lines[i][col]."""
    depth = 0
    for j in range(i, min(i + 20, len(lines))):
        for c in lines[j][col if j == i else 0:]:
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    return j
    return i


def line_map(root, src):
    pattern = re.compile(r'\b(%s)\s*\(' % '|'.join(sorted(SINKS, key=len, reverse=True)))
    args = ['-target', 'armv7-none-eabi', '-nostdinc', '-fno-short-enums', *OPENSSL_FLAGS,
            *include_args(root, src)]
    index = ci.Index.create()
    out = {}
    crypto = os.path.join(src, 'crypto')
    for dirpath, _, files in os.walk(crypto):
        for name in sorted(files):
            if not name.endswith('.c'):
                continue
            path = os.path.join(dirpath, name)
            lines = open(path, errors='replace').read().split('\n')
            uses = [(_macro_end(lines, i, m.start()) + 1, SINKS[m.group(1)])
                    for i, s in enumerate(lines) for m in pattern.finditer(s)]
            if not uses:
                continue
            tu = index.parse(path, args=args)
            funcs = [(c.extent.start.line, c.extent.end.line, c.spelling,
                      c.storage_class == ci.StorageClass.STATIC)
                     for c in tu.cursor.get_children()
                     if c.kind == ci.CursorKind.FUNCTION_DECL and c.is_definition()
                     and c.location.file and c.location.file.name == path]
            rows = []
            for line, sink in uses:
                f = next((f for f in funcs if f[0] <= line <= f[1]), None)
                if f:
                    rows.append([line, sink, f[2], f[3]])
            out[os.path.relpath(path, src)] = rows
    return out


def prototypes(text):
    """Function name -> declaration text, for every function declared in the preprocessed header text."""
    index = ci.Index.create()
    tu = index.parse('h.h', args=['-x', 'c', '-target', 'armv7-none-eabi', '-fno-short-enums'],
                     unsaved_files=[('h.h', text)])
    raw = text.encode()
    out = {}
    for c in tu.cursor.get_children():
        if c.kind == ci.CursorKind.FUNCTION_DECL and c.spelling not in out:
            decl = raw[c.extent.start.offset:c.extent.end.offset].decode()
            out[c.spelling] = ' '.join(decl.split()) + ';'
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--tarball', required=True)
    ap.add_argument('--edk2', required=True, help='edk2 git repository')
    ap.add_argument('--rev', default=EDK2_REV)
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as root:
        src = unpack(a.tarball, a.edk2, a.rev, root)
        header = '\n'.join(s for s in preprocess(root, src, ['-P', *IDA_DEFINES]).split('\n')
                           if s.strip() and not s.startswith('extern UINT8 _VerifySizeof')) + '\n'
        vals = defines(root, src)
        db = {'lines': line_map(root, src), 'err': err_table(src, vals),
              'asn1_items': sorted(set(re.findall(r'\bconst ASN1_ITEM (\w+)_it\b', header))),
              'prototypes': prototypes(header)}
    rev = sh('git', '-C', a.edk2, 'rev-parse', a.rev).strip()
    with open(os.path.join(HERE, 'securet30sec_openssl.h'), 'w') as f:
        f.write('/* Generated by gen_securet30sec_openssl.py from openssl-0.9.8l.tar.gz and edk2 %s. */\n' % rev)
        f.write(header)
    with open(os.path.join(HERE, 'securet30sec_openssl.json'), 'w') as f:
        json.dump({'edk2': rev, **db}, f, indent=0, sort_keys=True)
        f.write('\n')
    print('wrote %d sink lines in %d files, %d ERR function codes, %d ASN1 items, %d prototypes' % (
        sum(len(v) for v in db['lines'].values()), len(db['lines']),
        sum(len(v) for v in db['err'].values()), len(db['asn1_items']), len(db['prototypes'])))


if __name__ == '__main__':
    main()
