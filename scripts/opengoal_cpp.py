#!/usr/bin/env python3
"""Experimental pre-allocation OpenGOAL IR -> C++ continuation backend.

Consumes ir_probe.cpp output. Only a deliberately narrow integer/call subset is
supported. Unknown instructions fail; no machine stack copying or inline asm is
implemented. The JSON and generated C++ from game source must remain ignored.
"""
import argparse
import json
from pathlib import Path
import re

REG = r'igpr-(\d+)'
SERVICES = ['eco-current-time', 'eco-suspend', 'eco-load-duration']


def emit(document, entry):
    functions = {f['name']: f for f in document['functions']}
    if len(functions) != len(document['functions']):
        raise ValueError('duplicate function identity')
    if any(name in functions for name in SERVICES):
        raise ValueError('host service cannot be replaced by an input function')
    if entry not in functions:
        raise ValueError('entry function missing')
    selected = {}
    pending = [entry]
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        if name not in functions:
            raise ValueError('missing function: ' + name)
        selected[name] = functions[name]
        for instruction in functions[name]['instructions']:
            match = re.fullmatch(r"mov igpr-\d+, '([^ ]+)", instruction['text'])
            if match and match[1] not in SERVICES:
                pending.append(match[1])
    names = list(selected) + SERVICES
    ids = {name: i + 1 for i, name in enumerate(names)}
    blocks = []
    for name, function in selected.items():
        cases = []
        count = len(function['instructions'])
        for pc, instruction in enumerate(function['instructions']):
            text = instruction['text']
            if instruction['assembly_family']:
                raise ValueError(f'{name}:{pc}: assembly-family IR requires semantic lowering: {text}')
            code = None
            if text in ('null', 'value-reset'):
                code = 'break;'
            elif m := re.fullmatch(r'mov '+REG+', '+REG, text):
                code = f'f.r[{m[1]}] = f.r[{m[2]}]; break;'
            elif m := re.fullmatch(r'mov-ic '+REG+r', (-?\d+)', text):
                code = f'f.r[{m[1]}] = uint64_t({m[2]}); break;'
            elif m := re.fullmatch(r"mov "+REG+r", '([^ ]+)", text):
                code = f'f.r[{m[1]}] = {ids[m[2]]}; break;'
            elif m := re.fullmatch(r"mov-symptr "+REG+r", '#f", text):
                code = f'f.r[{m[1]}] = 4096; break;'
            elif m := re.fullmatch(r'(addi|subi) '+REG+', '+REG, text):
                operator = '+=' if m[1] == 'addi' else '-='
                code = f'f.r[{m[2]}] {operator} f.r[{m[3]}]; break;'
            elif m := re.fullmatch(r'goto label-(\d+)', text):
                if not 0 <= int(m[1]) < count:
                    raise ValueError('branch outside function')
                code = f'f.pc = {m[1]}; break;'
            elif m := re.fullmatch(r'j\('+REG+r' < '+REG+r'\) label-(\d+)', text):
                if not 0 <= int(m[3]) < count:
                    raise ValueError('branch outside function')
                code = f'if (int64_t(f.r[{m[1]}]) < int64_t(f.r[{m[2]}])) f.pc = {m[3]}; break;'
            elif m := re.fullmatch(r'call '+REG+r' \(ret '+REG+r'\) \(args(.*?)\)', text):
                args = [int(x) for x in re.findall(REG, m[3])]
                if m[3].strip() != ' '.join('igpr-'+str(x) for x in args):
                    raise ValueError('unsupported call arguments')
                values = ','.join('f.r['+str(x)+']' for x in args)
                code = f'call(f.r[{m[1]}], {m[2]}, {{{values}}}); break;'
            elif m := re.fullmatch(r'ret '+REG+' '+REG, text):
                code = f'finish(f.r[{m[2]}]); break;'
            if code is None:
                raise ValueError(f'{name}:{pc}: unsupported IR: {text}')
            # Register indices are bounded by the emitted frame, not silently truncated.
            if any(int(r) >= 256 for r in re.findall(REG, text)):
                raise ValueError('register limit exceeded')
            cases.append(f'case {pc}: {code}')
        blocks.append(f'case {ids[name]}: switch(f.pc++) {{\n'+ '\n'.join(cases)+'\ndefault: throw std::runtime_error("invalid pc"); } break;')
    labels = ','.join(json.dumps(n) for n in ['invalid'] + names)
    template = (Path(__file__).resolve().parents[1] / 'experiments/opengoal/host.cpp.in').read_text()
    return (template.replace('@BLOCKS@', '\n'.join(blocks))
            .replace('@LABELS@', labels).replace('@ENTRY@', str(ids[entry]))
            .replace('@CLOCK@', str(ids[SERVICES[0]]))
            .replace('@SUSPEND@', str(ids[SERVICES[1]]))
            .replace('@LOAD@', str(ids[SERVICES[2]])))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--entry', default='eco-entry')
    args = parser.parse_args()
    try:
        code = emit(json.loads(args.input.read_text()), args.entry)
    except (ValueError, KeyError) as error:
        parser.exit(1, str(error)+'\n')
    # Write only after the complete graph has passed validation.
    with args.output.open('x') as output:
        output.write(code)


if __name__ == '__main__':
    main()
