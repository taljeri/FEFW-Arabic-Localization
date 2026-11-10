#!/usr/bin/env python3
"""Patch a file inside a DMROMFS1 image IN PLACE, at identical byte size.

The image records (offset, size) per file, so a replacement must occupy exactly
the original size. A zstd stream can be padded with skippable frames
(0x184D2A5x + u32 length + data), which decompressors ignore, so any replacement
whose compressed form is <= the original fits without touching the index — no
27 GB rebuild and no extra disk.

  python3 romfs_patch.py list   <img> <prefix>
  python3 romfs_patch.py get    <img> <path> <outfile>
  python3 romfs_patch.py put    <img> <path> <newfile>   # pads to the original size
  python3 romfs_patch.py restore <img> <path> <backupfile>
"""
import struct, sys, os

MAGIC = b'DMROMFS1'


def read_index(img):
    """{path: (is_dir, offset, size)} — via the repo's own reader, which is correct
    about this format's index layout."""
    import sys
    sys.path.insert(0, '/Users/littledino/Documents/DSH-testing workspace/nxnative/dm/tools')
    import romfs_image
    return romfs_image.read_index(img)


def pad_to(data, size):
    """Pad a zstd stream to exactly `size` with skippable frames."""
    if len(data) > size:
        raise SystemExit(f'compressed {len(data)} > slot {size}: does not fit')
    out = bytearray(data)
    while len(out) < size:
        room = size - len(out)
        if room < 8:
            raise SystemExit(f'cannot pad {room} trailing bytes')
        chunk = min(room - 8, 1 << 20)
        out += struct.pack('<II', 0x184D2A50, chunk) + b'\x00' * chunk
    return bytes(out)


def main():
    cmd, img = sys.argv[1], sys.argv[2]
    idx = read_index(img)
    if cmd == 'list':
        pre = sys.argv[3]
        for k in sorted(idx):
            if k.startswith(pre):
                d, off, size = idx[k]
                print(f'{"dir " if d else "file"} {off:>12} {size:>10}  {k}')
        return
    path = sys.argv[3]
    if path not in idx:
        raise SystemExit(f'no such entry: {path}')
    is_dir, off, size = idx[path]
    if is_dir:
        raise SystemExit('is a directory')
    if cmd == 'get':
        with open(img, 'rb') as f:
            f.seek(off); data = f.read(size)
        open(sys.argv[4], 'wb').write(data)
        print(f'got {path}: {size} bytes -> {sys.argv[4]}')
    elif cmd == 'put':
        new = open(sys.argv[4], 'rb').read()
        blob = pad_to(new, size)
        with open(img, 'r+b') as f:
            f.seek(off); f.write(blob)
        print(f'put {path}: {len(new)} -> slot {size} (padded)')
    elif cmd == 'restore':
        old = open(sys.argv[4], 'rb').read()
        if len(old) != size:
            raise SystemExit(f'backup is {len(old)} bytes, slot is {size}')
        with open(img, 'r+b') as f:
            f.seek(off); f.write(old)
        print(f'restored {path}: {size} bytes')
    else:
        raise SystemExit(__doc__)


if __name__ == '__main__':
    main()
