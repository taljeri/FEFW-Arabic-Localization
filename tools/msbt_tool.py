#!/usr/bin/env python3
"""MSBT (MsgStdBn) read/write for the Arabic FEFW translation.

Format as found in this game's files (verified against Msg/USen/*.msbt.zst):

  header   0x00 'MsgStdBn', 0x0E u16 section count, 0x12 u32 file size
  sections at 0x20, each: tag(4) size(4) then body
  TXT2     0x10 u32 count, 0x14 u32 offsets[count], then the string data.
           Offsets are relative to the section start + 0x10, so offset[0] is
           4 + 4*count. Strings are UTF-8, NUL-terminated.
  escapes  0x0E <type> <params...>  inline reference/function tag
           0x0D                     line break
           Text runs are what a translator touches; controls are copied through.

Only TXT2 is rewritten, so LBL1 (labels) stays byte-identical and the string
count/order must not change.

  python3 msbt_tool.py extract <dir> <out.json>
  python3 msbt_tool.py inject  <dir> <in.json> <outdir>
  python3 msbt_tool.py verify  <dir> <outdir>
  python3 msbt_tool.py stats   <dir>
"""
import json, re, struct, sys, os, glob

KNOWN = (b'LBL1', b'ATO1', b'ATR1', b'TSY1', b'TXT2', b'GRP1')


def sections(d):
    """[(tag, offset, size)] in file order.

    LBL1's declared size under-runs its own label-string table by up to 16 bytes
    in these files, so walking size-by-size drifts. Tags are located directly and
    each section's extent runs to the next tag (or end of file).
    """
    found = []
    for tag in KNOWN:
        i = d.find(tag, 0x20)
        if i >= 0:
            found.append((i, tag))
    found.sort()
    return [(tag, off, (found[k + 1][0] if k + 1 < len(found) else len(d)) - off)
            for k, (off, tag) in enumerate(found)]


def txt2_of(d):
    for tag, off, size in sections(d):
        if tag == b'TXT2':
            return off, size
    raise ValueError('no TXT2 section')


def read_txt2(d, off, size):
    """Strings of a TXT2 section, in order, as raw bytes.

    Sliced by the offset table, not by a NUL scan: escape sequences carry their
    parameters inline and contain 0x00 bytes (0x0E <type> <u32> ...), so a NUL
    scan truncates the string. One trailing NUL terminator is dropped.
    """
    count = struct.unpack_from('<I', d, off + 0x10)[0]
    rel = [struct.unpack_from('<I', d, off + 0x14 + 4 * i)[0] for i in range(count)]
    out = []
    for i, r in enumerate(rel):
        p = off + 0x10 + r
        end = off + 0x10 + rel[i + 1] if i + 1 < count else off + size
        raw = d[p:end]
        if i + 1 == count:
            # The last string runs to the section end, which carries the writer's
            # alignment fill (0xAB, 0xFE, 0xFF, 0x00 observed). Strip the trailing
            # run of bytes >= 0xFE and 0xAB/0x00 fill, then one NUL terminator.
            while raw and (raw[-1] >= 0xFE or raw[-1] == 0xAB or raw[-1] == 0x00):
                raw = raw[:-1]
        elif raw.endswith(b'\x00'):
            raw = raw[:-1]
        out.append(raw)
    return out


def write_txt2(raw_strings):
    """A TXT2 section from raw byte strings (already UTF-8 + escapes)."""
    n = len(raw_strings)
    data = bytearray()
    rel = []
    base = 4 + 4 * n                      # offsets are relative to section+0x10
    for s in raw_strings:
        rel.append(base + len(data))
        data += s + b'\x00'
    size = 0x10 + 4 * n + len(data)
    pad = (-size) % 4
    out = bytearray()
    out += b'TXT2' + struct.pack('<I', size + pad)
    out += b'\x00' * 8
    out += struct.pack('<I', n)
    for r in rel:
        out += struct.pack('<I', r)
    out += data
    out += b'\x00' * pad
    return bytes(out)


def rebuild(d, raw_strings):
    secs = sections(d)
    new = write_txt2(raw_strings)
    out = bytearray(d[:0x20])
    for tag, off, size in secs:
        out += new if tag == b'TXT2' else d[off:off + size]
    struct.pack_into('<H', out, 0x0E, len(secs))
    struct.pack_into('<I', out, 0x12, len(out))
    return bytes(out)


def read_file(path):
    try:
        import backports.zstd as zstd
    except ImportError:
        import zstandard as zstd
    return zstd.decompress(open(path, 'rb').read())


def write_file(path, data):
    try:
        import backports.zstd as zstd
    except ImportError:
        import zstandard as zstd
    open(path, 'wb').write(zstd.compress(data, level=19))




CTRL = re.compile(r'\{c:([0-9a-fA-F]*)\}')

def decode(raw):
    """raw bytes -> editable text, losslessly and in one pass.

    Control bytes (below 0x20: the 0x0E/0x0D escapes and their parameters) and any
    byte that is not part of valid UTF-8 become {c:hex} tokens; valid UTF-8 stays
    text. Exactly reversible by encode(), whatever the file holds.
    """
    out, i, n = [], 0, len(raw)
    while i < n:
        b = raw[i]
        if b < 0x20:
            j = i
            while j < n and raw[j] < 0x20:
                j += 1
            out.append('{c:' + raw[i:j].hex() + '}')
            i = j
            continue
        if b < 0x80:
            out.append(chr(b)); i += 1; continue
        ln = 2 if b < 0xE0 else 3 if b < 0xF0 else 4 if b < 0xF8 else 0
        if ln and i + ln <= n:
            try:
                out.append(raw[i:i + ln].decode('utf-8')); i += ln; continue
            except UnicodeDecodeError:
                pass
        out.append('{c:%02x}' % b); i += 1
    return ''.join(out)


def encode(s):
    """editable text -> raw bytes; {c:hex} tokens go back to their bytes."""
    out, pos = bytearray(), 0
    for m in CTRL.finditer(s):
        out += s[pos:m.start()].encode('utf-8')
        out += bytes.fromhex(m.group(1))
        pos = m.end()
    out += s[pos:].encode('utf-8')
    return bytes(out)


def cmd_extract(d, out):
    res = {}
    for p in sorted(glob.glob(os.path.join(d, '*.msbt.zst'))):
        f = read_file(p)
        off, size = txt2_of(f)
        res[os.path.basename(p)] = [decode(s) for s in read_txt2(f, off, size)]
    json.dump(res, open(out, 'w'), ensure_ascii=False, indent=1)
    print(f'extracted {len(res)} files, {sum(len(v) for v in res.values()):,} strings -> {out}')


def cmd_inject(d, inp, outdir):
    tr = json.load(open(inp))
    os.makedirs(outdir, exist_ok=True)
    n = 0
    for p in sorted(glob.glob(os.path.join(d, '*.msbt.zst'))):
        name = os.path.basename(p)
        f = read_file(p)
        if name in tr:
            off, size = txt2_of(f)
            have = read_txt2(f, off, size)
            want = [encode(s) for s in tr[name]]
            if len(want) != len(have):
                sys.exit(f'[RED] {name}: {len(want)} strings, file has {len(have)}')
            f = rebuild(f, want)
        write_file(os.path.join(outdir, name), f)
        n += 1
    print(f'wrote {n} files -> {outdir}')


def cmd_verify(d, outdir):
    bad = 0
    for p in sorted(glob.glob(os.path.join(d, '*.msbt.zst'))):
        name = os.path.basename(p)
        a, b = read_file(p), read_file(os.path.join(outdir, name))
        sa, sb = sections(a), sections(b)
        if [t for t, _, _ in sa] != [t for t, _, _ in sb]:
            print('section mismatch', name); bad += 1; continue
        for (t, o1, s1), (_, o2, s2) in zip(sa, sb):
            if t != b'TXT2' and a[o1:o1 + s1] != b[o2:o2 + s2]:
                print('untouched section differs', t, name); bad += 1
        # strings must read back identically
        if read_txt2(a, *txt2_of(a)) != read_txt2(b, *txt2_of(b)):
            print('string mismatch', name); bad += 1
    print(f'verify: {bad} problems')


def cmd_stats(d):
    files = sorted(glob.glob(os.path.join(d, '*.msbt.zst')))
    n = chars = 0
    for p in files:
        f = read_file(p)
        strs = read_txt2(f, *txt2_of(f))
        n += len(strs); chars += sum(len(s) for s in strs)
    print(f'files {len(files)}  strings {n:,}  bytes {chars:,}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == 'extract': cmd_extract(sys.argv[2], sys.argv[3])
    elif cmd == 'inject': cmd_inject(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == 'verify': cmd_verify(sys.argv[2], sys.argv[3])
    elif cmd == 'stats': cmd_stats(sys.argv[2])
    else: sys.exit(__doc__)
