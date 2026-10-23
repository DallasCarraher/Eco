#!/usr/bin/env python3
"""Build the IR diagnostic with an already built local OpenGOAL Ninja tree.

Does not alter upstream sources. Compile/link flags come from goalc's own target.
Outputs and build-command logs belong in ignored directories.
"""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build, output = args.build.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).resolve().parents[1] / 'experiments/opengoal/ir_probe.cpp'
    commands = subprocess.check_output(['ninja', '-t', 'commands', 'goalc'], cwd=build, text=True).splitlines()
    compile_command = next(shlex.split(c) for c in commands if ' -c ' in c and c.endswith('/goalc/main.cpp'))
    source_index = compile_command.index('-c') + 1
    old_object = compile_command[compile_command.index('-o') + 1]
    compile_command[source_index] = str(source)
    compile_command[compile_command.index('-o') + 1] = str(output / 'probe.o')
    # Dependency records must not overwrite goalc's own records.
    for flag in ('-MT', '-MF'):
        index = compile_command.index(flag)
        del compile_command[index:index + 2]
    compile_command.remove('-MD')
    link_command = shlex.split(commands[-1])
    if link_command[:2] != [':', '&&'] or link_command[-2:] != ['&&', ':']:
        raise ValueError('unrecognized Ninja link command; refusing shell execution')
    link_command = link_command[2:-2]
    link_command[link_command.index(old_object)] = str(output / 'probe.o')
    link_command[link_command.index('-o') + 1] = str(output / 'ir-probe')
    measurements = []
    for name, command in [('compile', compile_command), ('link', link_command)]:
        start = time.monotonic()
        with (output / (name + '.log')).open('wb') as log:
            result = subprocess.run(command, cwd=build, stdout=log, stderr=subprocess.STDOUT, timeout=60)
        measurements.append(dict(stage=name, argv=command, exit_code=result.returncode,
                                 wall_seconds=time.monotonic() - start))
        (output / 'build.json').write_text(json.dumps(measurements, indent=2) + '\n')
        if result.returncode:
            return result.returncode
    print(output / 'ir-probe')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
