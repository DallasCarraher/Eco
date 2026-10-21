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
    parser.add_argument('--timeout', type=int, default=900, help='total build/run timeout in seconds')
    args = parser.parse_args()
    iso = args.iso.expanduser().resolve(strict=True)
    if not iso.is_file() or args.timeout <= 0:
        parser.error('provide an ISO file and a positive timeout')
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
                  'upstream_revision': subprocess.check_output(
                      ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  'status': 'disc_inspected', 'gameplay_verified': False}
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
               '--frames', '600', '--rounds', '2']
    if not args.web:
        command.append('--native-only')
    env = dict(os.environ)
    env['PATH'] = '/opt/homebrew/bin:' + env.get('PATH', '')
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
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    print('Logs:', out / 'pipeline.log')
    print('A successful pipeline does not establish gameplay compatibility.')
    if report['status'] != 'pipeline_finished':
        sys.exit(1)


if __name__ == '__main__':
    main()
