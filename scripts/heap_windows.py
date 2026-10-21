#!/usr/bin/env python3
"""Capture missed executable pages outside the boot ELF from a halted RAM dump.

Experimental fixed-address snapshots, not a general GOAL object loader. Only
observed, aligned miss addresses in PS2 main RAM are considered. The recompiler
and runtime validate the translated instruction words against live memory.
"""
import argparse
import binascii
from pathlib import Path
import re
import struct

from windows import UNIT, load_phdrs

RAM_SIZE = 32 * 1024 * 1024


def goal_function_entries(ram):
    """Use Jak 1's reciprocal type/symbol records to find tagged functions.

    Original Jak 1 uses SymInfo at symbol + (8167 * 8 - 4). A SymInfo holds a
    hash and a GOAL string pointer; a type points back to its defining symbol.
    Require both directions and the exact length-prefixed name before using
    a pointer as the function type. Never infer code from an opcode pattern.
    """
    tags = set()
    start = 0
    while True:
        text = ram.find(b'function\0', start, RAM_SIZE)
        if text < 0:
            break
        start = text + 1
        if text < 4 or struct.unpack_from('<I', ram, text - 4)[0] != 8:
            continue
        string_pointer = struct.pack('<I', text - 4)
        ref = 0
        while True:
            ref = ram.find(string_pointer, ref, RAM_SIZE)
            if ref < 0:
                break
            symbol = ref - 4 - (8167 * 8 - 4)
            ref += 1
            if symbol & 3 or not 0x10000 <= symbol < RAM_SIZE - 4:
                continue
            tag = struct.unpack_from('<I', ram, symbol)[0]
            if tag & 15 != 4 or not 0x10000 <= tag < RAM_SIZE - 4:
                continue
            if struct.unpack_from('<I', ram, tag)[0] == symbol:
                tags.add(tag)
    entries = set()
    for tag in tags:
        needle = struct.pack('<I', tag)
        at = 0
        while True:
            at = ram.find(needle, at, RAM_SIZE - 4)
            if at < 0:
                break
            # Retail Jak 1 function headers can be 8-byte aligned (including
            # addresses ending in 8), rather than OpenGOAL's 16-byte layout.
            if at % 8 == 0 and at >= 0x10000:
                entries.add(at + 4)
            at += 1
    return sorted(entries)


def capture(elf, ram, out, misses, goal_functions=False):
    if len(ram) < RAM_SIZE:
        raise ValueError('expected at least 32 MiB of main RAM in the dump')
    segments = [(h[2], h[2] + h[5]) for h in load_phdrs(elf) if h[0] == 1]
    tokens = misses.read_text().split() if misses.exists() else []
    if goal_functions:
        tokens = list(dict.fromkeys(tokens + [f'{pc:x}' for pc in goal_function_entries(ram)]))
    pages = {}
    for token in tokens:
        if ':' in token:
            # A known page can receive more code, or be reused by the loader.
            # Re-capture the live bytes at a module miss, not its old snapshot.
            match = re.fullmatch(r'([0-9A-Fa-f]{8})_[0-9A-Fa-f]{8}:([0-9A-Fa-f]+)', token)
            name = token.split(':', 1)[0]
            if not match or not (out / (name + '.bin')).is_file():
                continue
            if (out / (name + '.bin')).stat().st_size not in (UNIT, 2 * UNIT):
                continue
            offset = int(match[2], 16)
            if offset >= (out / (name + '.bin')).stat().st_size:
                continue
            pc = int(match[1], 16) + offset
        else:
            pc = int(token, 16)
        if pc & 3 or not (0x10000 <= pc < RAM_SIZE):
            continue
        if any(lo <= pc < hi for lo, hi in segments):
            continue
        base = pc & ~(UNIT - 1)
        # Include the next page: a function or its branch delay slot can
        # cross the 16 KiB translation boundary.
        blob = ram[base:min(base + 2 * UNIT, RAM_SIZE)]
        if not any(blob):
            continue
        stem = f'{base:08X}_{binascii.crc32(blob) & 0xffffffff:08X}'
        pages[token] = f'{stem}:{pc - base:x}'
        out.mkdir(parents=True, exist_ok=True)
        target = out / (stem + '.bin')
        if target.exists():
            if target.read_bytes() != blob:
                raise ValueError('snapshot hash collision: ' + str(target))
        else:
            target.write_bytes(blob)
            print(f'captured {stem}, {len(blob)} bytes (observed heap entry {pc:08X})')
    if pages:
        misses.write_text('\n'.join(pages.get(t, t) for t in tokens) + '\n')
    return len(pages)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf', type=Path)
    parser.add_argument('ram', type=Path)
    parser.add_argument('out', type=Path)
    parser.add_argument('misses', type=Path)
    parser.add_argument('--goal-functions', action='store_true', help='also seed linked Jak 1 function objects from type metadata')
    args = parser.parse_args()
    capture(args.elf.read_bytes(), args.ram.read_bytes(), args.out, args.misses, args.goal_functions)


if __name__ == '__main__':
    main()
