#!/usr/bin/env python3
"""Validate a local Jak 1 ISO, then optionally run a bounded recompilation probe."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from disc import Image

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('iso', type=Path)
    parser.add_argument('--run', action='store_true', help='compile and explore natively')
    parser.add_argument('--web', action='store_true', help='also build WASM (implies --run)')
    parser.add_argument('--capture-heap', action='store_true', help='experimental fixed-address heap code snapshots')
    parser.add_argument('--goal-functions', action='store_true', help='also seed linked Jak 1 function objects (implies --capture-heap)')
    parser.add_argument('--rounds', type=int, default=2)
    parser.add_argument('--frames', type=int, default=600)
    parser.add_argument('--timeout', type=int, default=900, help='total build/run timeout in seconds')
    args = parser.parse_args()
    args.capture_heap = args.capture_heap or args.goal_functions
    iso = args.iso.expanduser().resolve(strict=True)
    if not iso.is_file() or min(args.timeout, args.rounds, args.frames) <= 0:
        parser.error('provide an ISO file and positive timeout, rounds and frames')
    image = Image(iso)
    try:
        files = list(image.files())
        cnf = next((f for f in files if f[0].upper() == 'SYSTEM.CNF'), None)
        if cnf is None:
            parser.error('disc has no SYSTEM.CNF')
        image.file.seek(cnf[2] * 2048)
        text = image.file.read(cnf[3]).decode('ascii', 'replace')
        match = re.search(r'^BOOT2\s*=\s*(.+)$', text, re.MULTILINE | re.IGNORECASE)
        if not match:
            parser.error('SYSTEM.CNF has no BOOT2')
        boot = match[1].strip()
        names = {f[0].upper() for f in files}
        if not {'CGO/KERNEL.CGO', 'DGO/VI1.DGO'}.issubset(names):
            parser.error('expected Jak 1 CGO/KERNEL.CGO and DGO/VI1.DGO; refusing to label this disc Jak 1')
        report = {'iso': str(iso), 'boot': boot, 'volume': image.layers[0].volume,
                  'dgo_count': sum(n.endswith('.DGO') for n in names),
                  'source_revision': subprocess.check_output(
                      ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  'working_tree_dirty': bool(subprocess.check_output(
                      ['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip()),
                  'status': 'disc_inspected', 'gameplay_verified': False,
                  'capture_heap': args.capture_heap, 'rounds': args.rounds,
                  'goal_functions': args.goal_functions,
                  'frames_per_round': args.frames}
    finally:
        image.file.close()
    out = ROOT / 'games/jak1'
    out.mkdir(parents=True, exist_ok=True)
    report_path = out / 'probe.json'
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2), flush=True)
    if not (args.run or args.web):
        return
    linked = out / 'disc.iso'
    if os.path.lexists(linked) and linked.resolve() != iso:
        parser.error('games/jak1/disc.iso already points at another image; use a fresh workspace')
    bash = Path('/opt/homebrew/bin/bash')
    if not bash.is_file():
        parser.error('install modern bash with brew install bash')
    command = [str(bash), str(ROOT / 'scripts/port.sh'), 'jak1', str(iso),
               '--frames', str(args.frames), '--rounds', str(args.rounds)]
    if args.capture_heap:
        command.append('--capture-heap')
    if args.goal_functions:
        command.append('--goal-functions')
    if not args.web:
        command.append('--native-only')
    env = dict(os.environ)
    env['PATH'] = '/opt/homebrew/bin:' + env.get('PATH', '')
    if args.capture_heap:
        # Heap code is relocated and rewritten. Require every compiled word
        # to match at dispatch instead of upstream's sampled validation.
        env['PS2_WINDOW_FULL'] = '1'
    # New process group lets a timeout stop the whole build/exploration tree.
    import signal
    with (out / 'pipeline.log').open('w') as log:
        proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log,
                                stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = proc.wait(timeout=args.timeout)
            report['pipeline_exit_code'] = code
            report['status'] = 'pipeline_finished' if code == 0 else 'pipeline_failed'
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            report['status'] = 'pipeline_timeout'
    explore = out / 'explore.log'
    if explore.exists():
        log = explore.read_text(errors='replace')
        report['halts'] = re.findall(r'^\[ee\] halted: (.+)$', log, re.MULTILINE)
        report['missing_services'] = re.findall(r'^.*(?:unhandled syscall|\[iop\] missing).+$', log, re.MULTILINE)[:30]
        stops = re.findall(r'^\[ee\] stopped after (\d+) frames, (\d+) cycles: (.+)$', log, re.MULTILINE)
        if stops:
            frames, cycles, reason = stops[-1]
            report['last_run'] = {'frames': int(frames), 'cycles': int(cycles), 'reason': reason}
            if report['status'] == 'pipeline_finished':
                report['status'] = 'frame_limit_reached' if reason == 'frame limit reached' else 'runtime_halted'
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    print('Logs:', out / 'pipeline.log')
    print('A successful pipeline does not establish gameplay compatibility.')
    if report['status'] not in ('pipeline_finished', 'frame_limit_reached'):
        sys.exit(1)


if __name__ == '__main__':
    main()
