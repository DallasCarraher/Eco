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
    parser.add_argument('--live-template', action='store_true', help='test a pre-link template whose immediate is patched by the boot program')
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
    overlays = []
    if args.live_template:
        # Install an original test program at 0x180004. Patched LUI/ORI build
        # an address, ADDIU supplies 4, and SW/LW use a signed patched offset
        # to pass that value into v1 for the Exit syscall.
        payload = [0x3c0b0019, 0x356b0100, 0x240a0004, 0xad6afff0,
                   0x8d63fff0, 0x0000000c, 0x1000ffff, 0]
        boot = [0x3c080018]
        for index, word in enumerate(payload):
            boot.extend([0x3c090000 | (word >> 16), 0x35290000 | (word & 0xffff),
                         0xad090004 + 4 * index])
        boot.extend([0x25080004, 0x01000008, 0])
        code = struct.pack('<' + 'I' * len(boot), *boot)
        templates = game / 'templates'
        templates.mkdir(exist_ok=True)
        for suffix in ('.bin', '.live16'):
            (templates / ('00180000_TOPSMOKE' + suffix)).unlink(missing_ok=True)
        raw = [0] + [word & 0xffff0000 if index < 5 else word
                     for index, word in enumerate(payload)]
        (templates / '00000000_TOPSMOKE.bin').write_bytes(struct.pack('<' + 'I' * len(raw), *raw))
        (templates / '00000000_TOPSMOKE.live16').touch()
        overlays = ['--overlays', templates]
    ident = b'\x7fELF\x01\x01\x01' + bytes(9)
    header = struct.pack('<16sHHIIIIIHHHHHH', ident, 2, 8, 1, base,
                         52, 0, 0, 52, 32, 1, 0, 0, 0)
    segment = struct.pack('<8I', 1, 0x100, base, base, len(code), len(code), 5, 0x100)
    elf = game / 'core.elf'
    elf.write_bytes((header + segment).ljust(0x100, b'\0') + code)
    (game / 'disc/SYSTEM.CNF').write_text('BOOT2 = cdrom0:\\SMOKE.ELF;1\n')
    run([ROOT / 'build/tools/eerecomp', elf, *overlays, '--out', generated])
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
