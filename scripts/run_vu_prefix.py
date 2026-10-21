#!/usr/bin/env python3
"""Bounded, serial offline VU prefix comparison; no ISO, game boot or model calls."""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time

import run_experiments as harness

ROOT = Path(__file__).resolve().parents[1]
LIMIT_BYTES = 8 * 1024 * 1024
MIN_FREE = 10 * 1024**3
CASE_SECONDS = 900


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--runner', type=Path, required=True)
    parser.add_argument('--generated', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--continuations', type=int, default=8192, help='compiled prefix budget, 1..8192')
    args = parser.parse_args()
    if not 1 <= args.continuations <= 8192:
        parser.error('continuation budget must be 1..8192; the guard cannot be increased')
    args.snapshot = args.snapshot.resolve()
    args.runner = args.runner.resolve()
    args.generated = args.generated.resolve()
    args.output = args.output.resolve()
    if not args.output.is_relative_to(ROOT/'local/experiments') or args.output.exists():
        parser.error('output must be a new ignored local/experiments directory')
    if shutil.disk_usage(ROOT).free < MIN_FREE:
        parser.error('less than 10 GiB free')
    args.output.mkdir(parents=True)
    files = [Path(str(args.snapshot)+'-'+s) for s in ('code.bin', 'before.bin', 'memory.bin', 'meta.txt', 'pipe.bin')]
    generated = harness.inventory(args.generated)
    report = {'source_commit': harness.git('rev-parse', 'HEAD').decode().strip(),
              'source_diff_sha256': harness.digest(harness.git('diff', 'HEAD', '--binary')),
              'runner_sha256': harness.sha(args.runner), 'wrapper_sha256': harness.sha(Path(__file__)),
              'snapshot': {str(p): harness.sha(p) for p in files},
              'generated_sha256': harness.digest(harness.encoded(generated)),
              'generated_inventory': generated, 'cases': [], 'comparison': None,
              'limits': dict(seconds_per_case=CASE_SECONDS, output_bytes=LIMIT_BYTES,
                             min_free_bytes=MIN_FREE, compiled_continuations=args.continuations,
                             interpreter_instructions=1_000_000),
              'scope': 'one saved invocation prefix; no hardware oracle or exhaustive coverage',
              'state': 'running'}

    def save():
        harness.atomic(args.output/'report.json', report)

    # Reuse the harness' process-group cleanup. Signals always interrupt the wait.
    def cancel(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, cancel)
    signal.signal(signal.SIGINT, cancel)
    harness.enable_subreaper()
    env = {k: v for k, v in os.environ.items() if not k.startswith('PS2_')}

    def case(name, mode, instructions=None):
        prefix = args.output/name
        cmd = [str(args.runner), str(args.snapshot), mode, str(prefix)]
        if instructions is not None:
            cmd.append(str(instructions))
        result = {'name': name, 'argv': cmd, 'outcome': 'running'}
        report['cases'].append(result)
        save()
        start = time.monotonic()
        with (args.output/(name+'.log')).open('wb') as log:
            proc = subprocess.Popen(cmd, cwd=args.output, env=env, stdout=log, stderr=subprocess.STDOUT,
                                    start_new_session=True)
            try:
                while proc.poll() is None:
                    if time.monotonic()-start >= CASE_SECONDS:
                        result['outcome'] = 'timeout'
                        break
                    if harness.size(args.output) >= LIMIT_BYTES:
                        result['outcome'] = 'output_limit'
                        break
                    if shutil.disk_usage(ROOT).free < MIN_FREE:
                        result['outcome'] = 'disk_limit'
                        break
                    time.sleep(.05)
            except KeyboardInterrupt:
                result['outcome'] = 'cancelled'
                raise
            finally:
                harness.stop_group(proc)
                result.update(exit_code=proc.returncode, wall_seconds=time.monotonic()-start)
                save()
        status = Path(str(prefix)+'-status.json')
        if result['outcome'] != 'running':
            return None
        if proc.returncode not in (0, 4) or not status.is_file():
            result['outcome'] = 'process_failed'
            save()
            return None
        try:
            result['status'] = json.loads(status.read_text())
            if type(result['status']['complete']) is not bool or result['status']['complete'] != (proc.returncode == 0):
                raise ValueError('exit code and completion status disagree')
            for field in ('next_pc', 'issue_clock_delta', 'steps', 'npc'):
                if type(result['status'][field]) is not int or result['status'][field] < 0:
                    raise ValueError('invalid numeric status field')
        except (OSError, ValueError, KeyError, TypeError) as error:
            result.update(outcome='process_failed', status_error=str(error))
            save()
            return None
        result['outcome'] = 'complete' if result['status']['complete'] else 'partial_checkpoint'
        save()
        return result['status']

    save()
    try:
        a = case('compiled', 'compiled-prefix', args.continuations)
        if a is not None:
            steps = a['issue_clock_delta']
            if not 0 < steps < 1_000_000:
                report['state'] = 'interpreter_budget_not_applicable'
            else:
                b = case('interpreted', 'interpreted' if a['complete'] else 'interpreted-prefix',
                         None if a['complete'] else steps)
                if b is not None:
                    equality = {}
                    for suffix in ('regs.bin', 'mem.bin', 'packets.bin', 'pipe.txt'):
                        equality[suffix] = (args.output/('compiled-'+suffix)).read_bytes() == (args.output/('interpreted-'+suffix)).read_bytes()
                    report['comparison'] = {'exact_fields': equality,
                        'next_pc_equal': a['next_pc'] == b['next_pc'],
                        'issue_clock_equal': a['issue_clock_delta'] == b['issue_clock_delta'],
                        'full_invocation_compared': a['complete'] and b['complete'],
                        'interpreter_npc': b['npc'], 'interpreter_ending': b['ending']}
                    report['state'] = 'finished'
        if report['state'] == 'running':
            report['state'] = 'incomplete'
    except KeyboardInterrupt:
        report['state'] = 'cancelled'
    finally:
        report['output_bytes'] = harness.size(args.output)
        save()
    print(json.dumps({'state': report['state'], 'comparison': report['comparison']}, indent=2))
    comparison = report['comparison']
    return 0 if (report['state'] == 'finished' and comparison and
                 all(comparison['exact_fields'].values()) and comparison['next_pc_equal'] and
                 comparison['issue_clock_equal']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
