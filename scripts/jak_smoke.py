#!/usr/bin/env python3
"""Build a tiny original PS2 program to verify the native/WASM toolchain.

This is not Jak code and does not establish game compatibility.
"""
import argparse
from pathlib import Path
import shutil
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def run(args):
    subprocess.run([str(a) for a in args], cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--web', action='store_true', help='also compile the browser target')
    args = parser.parse_args()
    game = ROOT / 'games/toolchain-smoke'
    generated = ROOT / 'generated/toolchain-smoke'
    native = ROOT / 'build/native-toolchain-smoke'
    (game / 'disc').mkdir(parents=True, exist_ok=True)
    generated.mkdir(parents=True, exist_ok=True)

    # ELF32/MIPS, one executable PT_LOAD. Exit syscall uses v1 on the PS2.
    base = 0x100000
    # A backward branch after Exit lets the runtime reach its preemption check.
    code = struct.pack('<4I', 0x24030004, 0x0000000c, 0x1000ffff, 0)
    ident = b'\x7fELF\x01\x01\x01' + bytes(9)
    header = struct.pack('<16sHHIIIIIHHHHHH', ident, 2, 8, 1, base,
                         52, 0, 0, 52, 32, 1, 0, 0, 0)
    segment = struct.pack('<8I', 1, 0x100, base, base, len(code), len(code), 5, 0x100)
    elf = game / 'core.elf'
    elf.write_bytes((header + segment).ljust(0x100, b'\0') + code)
    (game / 'disc/SYSTEM.CNF').write_text('BOOT2 = cdrom0:\\SMOKE.ELF;1\n')
    run([ROOT / 'build/tools/eerecomp', elf, '--out', generated])
    run(['cmake', '-S', ROOT, '-B', native, '-G', 'Ninja',
         '-DCMAKE_BUILD_TYPE=Release', '-DPS2_GENERATED=' + str(generated)])
    run(['cmake', '--build', native, '--target', 'ps2run', '-j', '4'])
    result = subprocess.run([str(native / 'ps2run'), str(elf), '--frames', '2',
                             '--trace-syscalls'], cwd=ROOT, text=True,
                            capture_output=True, timeout=30, check=True)
    (game / 'native.log').write_text(result.stdout + result.stderr)
    if ('[ee] halted: Exit' not in result.stderr or
            not result.stderr.rstrip().endswith(': Exit') or
            'no translated code' in result.stderr):
        raise SystemExit('FAIL: fixture did not reach the PS2 Exit syscall; see ' + str(game / 'native.log'))
    print('PASS: original MIPS fixture translated, compiled and executed its Exit syscall.', flush=True)
    if args.web:
        shutil.copyfile(elf, game / 'disc/SMOKE.ELF')
        run(['hdiutil', 'makehybrid', '-iso', '-ov', '-o', game / 'disc.iso', game / 'disc'])
        run(['/opt/homebrew/bin/bash', ROOT / 'scripts/build_web.sh', 'toolchain-smoke'])
        wasm = ROOT / 'build/web-toolchain-smoke/ps2web.wasm'
        with wasm.open('rb') as src:
            assert src.read(8) == b'\0asm\x01\0\0\0', 'Invalid WASM header'
        print('PASS: browser target compiled to a valid WASM binary. Browser execution is a separate check.')


if __name__ == '__main__':
    main()
