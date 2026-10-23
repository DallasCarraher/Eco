#!/usr/bin/env python3
"""Read retail Jak 1 event markers from an existing private RAM dump.

No game execution. Layout facts use OpenGOAL's Jak 1 offset assertions, not
its PC runtime layout. A marker identifies state, not a visually aligned pose.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

RAM_SIZE = 32 * 1024 * 1024
SYMINFO = 8167 * 8 - 4


class Markers:
    def __init__(self, ram):
        self.ram = ram[:RAM_SIZE]
        self.symbol_type = None
        candidates = [s for s in self.candidates('symbol')
                      if self.u32(self.u32(s)) == s and self.u32(s-4) == self.u32(s)]
        if len(candidates) != 1:
            raise ValueError('no unique reciprocal symbol type')
        self.symbol_type = self.u32(candidates[0])
        false_symbols = self.candidates('#f')
        if len(false_symbols) != 1:
            raise ValueError('no unique false symbol')
        self.false_symbol = false_symbols[0]

    def u32(self, at):
        if not 0 <= at <= len(self.ram)-4:
            return 0
        return struct.unpack_from('<I', self.ram, at)[0]

    def field(self, obj, offset):
        # GOAL basic pointers point four bytes after the type word.
        return self.u32(obj+offset-4)

    def string(self, ptr):
        if not 0x10000 <= ptr < len(self.ram)-5:
            return None
        n = self.u32(ptr)
        if not 0 < n <= 256 or ptr+4+n >= len(self.ram):
            return None
        if self.ram[ptr+4+n] != 0:
            return None
        try:
            return self.ram[ptr+4:ptr+4+n].decode('ascii')
        except UnicodeDecodeError:
            return None

    def symbol_name(self, sym):
        if self.symbol_type is not None and self.u32(sym-4) != self.symbol_type:
            return None
        return self.string(self.u32(sym+SYMINFO+4))

    def candidates(self, name):
        start = 0
        found = set()
        while True:
            text = self.ram.find(name.encode()+b'\0', start)
            if text < 0:
                break
            start = text+1
            if self.u32(text-4) != len(name):
                continue
            needle = struct.pack('<I', text-4)
            ref = 0
            while True:
                ref = self.ram.find(needle, ref)
                if ref < 0:
                    break
                sym = ref-4-SYMINFO
                ref += 1
                if 0x10000 <= sym < len(self.ram)-4 and sym % 8 == 4:
                    if self.symbol_type is None or self.u32(sym-4) == self.symbol_type:
                        found.add(sym)
        return sorted(found)

    def value(self, name):
        candidates = self.candidates(name)
        if len(candidates) != 1:
            raise ValueError('no unique symbol: '+name)
        return self.u32(candidates[0])

    def active_objects(self, root):
        pending = [root]
        seen = set()
        while pending:
            obj = pending.pop()
            if obj in seen:
                raise ValueError('cycle or duplicate in active tree')
            if len(seen) >= 4096 or self.field(obj, 28) != obj:
                raise ValueError('invalid active-tree self link or size')
            seen.add(obj)
            link = self.field(obj, 20)
            siblings = set()
            while link not in (0, self.false_symbol):
                if link in siblings or len(siblings) >= 4096:
                    raise ValueError('invalid sibling chain')
                siblings.add(link)
                child = self.u32(link)
                if self.field(child, 24) != link:
                    raise ValueError('invalid process pointer backlink')
                pending.append(child)
                link = self.field(child, 16)
        return seen

    def report(self):
        root = self.value('*active-pool*')
        logo_type = self.value('logo')
        if self.symbol_name(self.u32(logo_type)) != 'logo':
            raise ValueError('logo type backlink differs')
        logos = []
        for obj in sorted(self.active_objects(root)):
            if self.u32(obj-4) != logo_type:
                continue
            state = self.field(obj, 56)
            anim = self.field(obj, 228)
            logos.append({'process': obj, 'name': self.symbol_name(self.field(obj, 4)),
                          'state': self.symbol_name(self.field(state, 4)),
                          'status': self.symbol_name(self.field(obj, 36)),
                          'anim': anim, 'anim_name_if_string': self.string(self.field(anim, 16)),
                          'anim_index': self.field(anim, 20), 'anim_parts': self.field(anim, 24)})
        art = self.value('*art-control*')
        return {'active_logo_processes': logos,
                'active_art_stream': self.string(self.field(art, 176)),
                'visual_alignment_verified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ram', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    local = Path(__file__).resolve().parents[1]/'local'
    output = args.output.resolve()
    if not output.is_relative_to(local) or output.exists():
        parser.error('output must be a new ignored local directory')
    ram = args.ram.read_bytes()
    if len(ram) < RAM_SIZE:
        parser.error('expected at least 32 MiB of main RAM')
    report = Markers(ram).report()
    report.update(ram_sha256=hashlib.sha256(ram).hexdigest(), ram_path=str(args.ram.resolve()))
    output.mkdir(parents=True)
    (output/'markers.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Markers written privately; no visual alignment inferred')


if __name__ == '__main__':
    main()
