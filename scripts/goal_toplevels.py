#!/usr/bin/env python3
"""Extract Jak 1 V3 object top-level code as local pre-link templates.

Templates enter at offset 4, relocate to the actual call site, keep opcodes and
registers fixed, and read supported immediates live after the original linker
patches them. The optional --fixed mode uses an observed boot heap top instead.
These outputs contain game code: never commit.
"""
import argparse
import binascii
from pathlib import Path
import struct

from disc import Image


def templates(archive, top):
    if len(archive) < 64:
        raise ValueError('truncated DGO header')
    count, = struct.unpack_from('<I', archive)
    at = 64
    for _ in range(count):
        if at + 64 > len(archive):
            raise ValueError('truncated object header')
        size, = struct.unpack_from('<I', archive, at)
        body = archive[at + 64:at + 64 + size]
        if len(body) != size:
            raise ValueError('truncated object body')
        at += 64 + ((size + 15) & ~15)
        if len(body) < 128:
            continue
        _, length, version, segments = struct.unpack_from('<4I', body)
        if version != 3 or segments != 3:
            continue
        _, offset, length_top, magic = struct.unpack_from('<4I', body, 80 + 2 * 16)
        if not length_top:
            continue
        if magic or length_top & 3 or length_top < 8:
            raise ValueError('unsupported top-level segment')
        data = body[length + offset:length + offset + length_top]
        if len(data) != length_top:
            raise ValueError('top-level segment outside object')
        base = (top - length_top) & ~15
        yield base, data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('iso', type=Path)
    parser.add_argument('out', type=Path)
    parser.add_argument('--top', type=lambda s: int(s, 0), default=0x017fc000)
    parser.add_argument('--fixed', action='store_true', help='diagnostic fixed-address templates instead of relocatable entry-relative templates')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    image = Image(args.iso)
    seen = set()
    try:
        for path, _, sector, size in image.files():
            if not path.upper().endswith(('.CGO', '.DGO')):
                continue
            image.file.seek(sector * 2048)
            for base, data in templates(image.file.read(size), args.top):
                if not args.fixed:
                    base = 0
                stem = f'{base:08X}_TOP{binascii.crc32(data) & 0xffffffff:08X}'
                if stem in seen:
                    continue
                seen.add(stem)
                (args.out / (stem + '.bin')).write_bytes(data)
                (args.out / (stem + '.live16')).touch()
    finally:
        image.file.close()
    print(f'{len(seen)} top-level templates written locally to {args.out}')


if __name__ == '__main__':
    main()
