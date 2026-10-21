#!/usr/bin/env python3
"""Bounded, serial native experiments. Standard library only; no network or builds."""
import argparse
from contextlib import ExitStack, contextmanager
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import selectors
import shutil
import signal
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
ENV_KEYS = {'PS2_WINDOW_FULL', 'PS2_GS', 'PS2_VU_INTERPRET', 'PS2_GS_COMPARE', 'PS2_VU_CHECK', 'PS2_VU_CHECK_CONTINUATIONS'}
STATUSES = {'frame_limit_reached', 'runtime_halted', 'timeout', 'process_failed',
            'unsupported', 'output_limit', 'disk_limit', 'cancelled', 'incomplete'}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as src:
        for block in iter(lambda: src.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def atomic(path, value):
    path = Path(path)
    temp = path.with_name(path.name + '.tmp')
    with temp.open('w') as out:
        out.write(value if isinstance(value, str) else json.dumps(value, indent=2, allow_nan=False) + '\n')
        out.flush()
        os.fsync(out.fileno())
    os.replace(temp, path)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def inventory(directory):
    return {str(p.relative_to(directory)): {'sha256': sha(p), 'bytes': p.stat().st_size}
            for p in sorted(Path(directory).rglob('*')) if p.is_file()}


def size(directory):
    return sum(p.stat().st_size for p in Path(directory).rglob('*') if p.is_file())


@contextmanager
def lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('resource locked: ' + str(path)) from None
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def manifest_read(path):
    m = json.loads(path.read_text())
    if m.get('schema_version') != 1:
        raise ValueError('unsupported manifest schema')
    d = m['defaults']
    for key in ('frames', 'frame_every', 'repetitions', 'case_timeout_seconds',
                'total_timeout_seconds', 'max_output_bytes', 'min_free_disk_bytes'):
        if type(d[key]) is not int or d[key] <= 0:
            raise ValueError(key + ' must be a positive integer')
    if d['concurrency'] != 1 or d['initial_memory_card'] != 'fresh_per_case':
        raise ValueError('only serial execution with fresh cards is supported')
    for kind in ('scenarios', 'variants'):
        entries = m[kind]
        if not entries or len({e['id'] for e in entries}) != len(entries):
            raise ValueError('empty or duplicate ' + kind)
        for e in entries:
            if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', e['id']):
                raise ValueError('unsafe case id')
    for e in [d] + m['variants']:
        env = e.get('environment', {})
        if not isinstance(env, dict) or set(env) - ENV_KEYS:
            raise ValueError('environment must use the PS2 setting allowlist')
        for key, value in env.items():
            if value not in ({'cpu', 'gpu', 'both'} if key == 'PS2_GS' else {'1', 'all'} if key == 'PS2_VU_CHECK' else {'8192', '16384'} if key == 'PS2_VU_CHECK_CONTINUATIONS' else {'1'}):
                raise ValueError('invalid setting ' + key)
    for v in m['variants']:
        env = d.get('environment', {}) | v.get('environment', {})
        if 'PS2_VU_CHECK_CONTINUATIONS' in env and env.get('PS2_VU_CHECK') != 'all':
            raise ValueError('continuation policy requires PS2_VU_CHECK=all')
        if env.get('PS2_WINDOW_FULL') != '1' or 'PS2_GS' not in env:
            raise ValueError('each case requires PS2_WINDOW_FULL=1 and explicit PS2_GS')
    buttons = 'select|l3|r3|start|up|right|down|left|l2|r2|l1|r1|triangle|circle|cross|square'
    for s in m['scenarios']:
        for press in s['presses']:
            if not re.fullmatch(r'[0-9]+:(?:' + buttons + r')(?:\+(?:' + buttons + r'))*:[1-9][0-9]*', press):
                raise ValueError('invalid press ' + press)
            start, _, count = press.split(':')
            if int(start) < 1 or int(start) + int(count) - 1 > d['frames']:
                raise ValueError('press outside case frames')
    return m


def cases(m, pilot=False):
    result = []
    for s in m['scenarios']:
        for v in m['variants']:
            for r in range(1, m['defaults']['repetitions'] + 1):
                result.append({'id': f"{s['id']}--{v['id']}--{r}", 'scenario': s['id'],
                               'variant': v['id'], 'repetition': r, 'presses': s['presses'],
                               'environment': m['defaults'].get('environment', {}) | v['environment']})
    if pilot:
        ids = ['boot-idle--gpu-compiled--1', 'boot-idle--gpu-compiled--2', 'boot-idle--cpu-compiled--1']
        by_id = {c['id']: c for c in result}
        return [by_id[i] for i in ids]
    return result


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def identities(args):
    # Include untracked source bytes, not just git diff (new runners count too).
    diff = git('diff', 'HEAD', '--binary')
    untracked = git('ls-files', '--others', '--exclude-standard', '-z').split(b'\0')
    extra = {os.fsdecode(p): sha(ROOT / os.fsdecode(p)) for p in untracked if p}
    generated = inventory(args.generated)
    if not generated:
        raise ValueError('generated-code inventory is empty')
    return {'source_commit': git('rev-parse', 'HEAD').decode().strip(),
            'source_dirty': bool(diff or extra),
            'source_dirty_sha256': digest(diff + encoded(extra)),
            'binary_sha256': sha(args.runner), 'generated_sha256': digest(encoded(generated)),
            'generated_inventory': generated, 'iso_sha256': sha(args.iso), 'elf_sha256': sha(args.elf),
            'manifest_sha256': sha(args.manifest), 'runner_script_sha256': sha(Path(__file__)),
            'paths': {k: str(getattr(args, k)) for k in ('runner', 'generated', 'iso', 'elf', 'manifest')}}


def metadata(args):
    tools = {'python': sys.version, 'platform': platform.platform(), 'machine': platform.machine(),
             'processor': platform.processor() or None}
    for name, cmd in [('compiler', ['c++', '--version']), ('cmake', ['cmake', '--version'])]:
        try:
            tools[name] = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=5).decode().splitlines()[0]
        except (OSError, subprocess.SubprocessError):
            tools[name] = None
    cache = args.runner.parent / 'CMakeCache.txt'
    tools['build_cache_sha256'] = sha(cache) if cache.is_file() else None
    tools['build_provenance'] = 'Local files fingerprinted; build-to-source provenance is not attested.'
    return tools


def parse_log(text, requested, frames, code):
    stops = re.findall(r'^\[ee\] stopped after (\d+) frames, (\d+) cycles: (.+)$', text, re.M)
    halts = re.findall(r'^\[ee\] halted: (.+)$', text, re.M)
    adapters = re.findall(r'^\[gpu\] (.+ \(.*\))$', text, re.M)
    gpu_stats = bool(re.search(r'^\[gpu\] \d+ submits, dispatches:', text, re.M))
    fallback = 'WebGPU unavailable, using the software renderer' in text
    backend = ('cpu' if fallback or requested == 'cpu' else
               ('both' if requested == 'both' else 'gpu') if adapters and gpu_stats else 'unknown')
    missing = re.search(r'missing code at (0x[0-9a-fA-F]+) \(ra (0x[0-9a-fA-F]+)\)', text)
    vu = re.findall(r'^\[vu-check-summary\] sampled (\d+) calls, (\d+) mismatches$', text, re.M)
    chain = re.findall(r'^\[vu-chain-summary\] compared (\d+) chains, (\d+) continuations, (\d+) interpreter fallbacks, (\d+) mismatches, (\d+) nonflag$', text, re.M)
    outcomes = re.findall(r'^\[vu-chain-outcomes\] attempted (\d+) complete (\d+) mismatch (\d+) budget_exhausted (\d+) unsupported (\d+) unchecked_tail_dispatches (\d+) checkpoints (\d+) continuations (\d+)$', text, re.M)
    outcome_markers = re.findall(r'^\[vu-chain-outcomes\].*$', text, re.M)
    outcome_counts = None
    if len(outcome_markers) == 1 and len(outcomes) == 1 and code == 0:
        values = list(map(int, outcomes[0]))
        if values[0] == sum(values[1:5]):
            outcome_counts = dict(zip(('attempted', 'complete_match', 'mismatch', 'budget_exhausted',
                                      'unsupported', 'unchecked_tail_dispatches', 'checkpoints', 'continuations'), values))
    status = 'incomplete'
    if code != 0:
        status = 'process_failed'
    elif len(stops) == 1 and len(re.findall(r'^\[ee\] stopped after.*$', text, re.M)) == 1:
        f, cycle, reason = stops[0]
        if reason == 'frame limit reached':
            if int(f) == frames and halts == [reason]:
                status = 'frame_limit_reached'
        elif int(f) <= frames and halts == [reason]:
            status = 'runtime_halted'
    # Unknown GPU evidence must never pass as a GPU comparison.
    if status in ('frame_limit_reached', 'runtime_halted') and requested != 'cpu' and backend not in ('gpu', 'both'):
        status = 'unsupported'
    return {'status': status, 'observed_backend': backend, 'gpu_adapter': adapters[-1] if adapters else None,
            'last_guest_frame': int(stops[-1][0]) if stops else None,
            'last_guest_cycle': int(stops[-1][1]) if stops else None,
            'halt_reason': stops[-1][2] if stops else (halts[-1] if halts else None),
            'first_missing_pc': missing[1] if missing else None, 'first_missing_ra': missing[2] if missing else None,
            'comparison_counts': {'sampled_last_observed': int(vu[-1][0]) if vu else None,
                                  'mismatches_last_observed': int(vu[-1][1]) if vu else None,
                                  'checked_final': None, 'skipped': None, 'eligible_total': None},
            'chain_comparison_outcomes': outcome_counts,
            'chain_comparison_complete_for_attempted': (bool(outcome_counts['attempted']) and
                outcome_counts['attempted'] == outcome_counts['complete_match'] and
                outcome_counts['unchecked_tail_dispatches'] == 0) if outcome_counts is not None else None,
            'chain_comparison_counts': dict(zip(('chains', 'continuations', 'interpreter_fallbacks', 'mismatches', 'nonflag'),
                                               map(int, chain[-1]))) if len(chain) == 1 and code == 0 else None,
            'gs_comparison_counts': [dict(pixels_over_runtime_delta_2=int(a), pixels=int(b), max_channel_delta=int(c))
                                     for a, b, c in re.findall(r'^\[gs\] gpu differs in (\d+) of (\d+) pixels \(max (\d+)\)$', text, re.M)],
            'backend_evidence': 'software fallback' if fallback else 'explicit CPU setting' if requested == 'cpu'
                                else 'adapter and GPU submit statistics' if adapters and gpu_stats else 'unavailable'}


def enable_subreaper():
    # Linux permits reaping orphaned grandchildren; macOS reaps them via launchd.
    if sys.platform.startswith('linux'):
        import ctypes
        if ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) != 0:
            raise OSError('cannot enable child subreaper')


def stop_group(proc, grace=1.0):
    def dead_group():
        # Darwin can return EPERM for killpg(..., 0) while an exited group is
        # being removed. Do not mistake this for a surviving writable child.
        rows = subprocess.check_output(['ps', '-axo', 'pgid=,stat='], text=True, timeout=5)
        members = [row.split()[1] for row in rows.splitlines()
                   if len(row.split()) == 2 and row.split()[0] == str(proc.pid)]
        return all(state.startswith('Z') for state in members)

    def send(sig):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            pass
        except PermissionError:
            if not dead_group():
                raise
    send(signal.SIGTERM)
    until = time.monotonic() + grace
    while time.monotonic() < until:
        proc.poll()
        try:
            os.killpg(proc.pid, 0)
        except ProcessLookupError:
            break
        except PermissionError:
            if dead_group():
                break
            raise
        time.sleep(.02)
    send(signal.SIGKILL)  # Even if the leader already exited, kill surviving children.
    proc.wait()
    if sys.platform.startswith('linux'):
        while True:
            try:
                os.waitpid(-proc.pid, 0)
            except ChildProcessError:
                break


def execute(args, spec, defaults, cancelled, remaining):
    directory = args.output / (spec['id'] + '--' + uuid.uuid4().hex[:12])
    directory.mkdir()
    (directory / 'frames').mkdir()
    argv = [str(args.runner), str(args.elf), '--disc', str(args.iso), '--frames', str(defaults['frames']),
            '--memcard', str(directory / 'card.ps2'), '--misses', str(directory / 'misses.txt'),
            '--frames-dir', str(directory / 'frames'), '--frame-every', str(defaults['frame_every'])]
    for p in spec['presses']:
        argv.extend(['--press', p])
    env = {k: v for k, v in os.environ.items() if not k.startswith('PS2_')}
    env.update(spec['environment'])
    report = dict(spec, directory=directory.name, argv=argv, start=now(), gameplay_verified=False)
    started = time.monotonic()
    forced = None
    proc = None
    log = directory / 'runtime.log'
    with log.open('wb') as out, selectors.DefaultSelector() as sel:
        try:
            proc = subprocess.Popen(argv, cwd=directory, env=env, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, start_new_session=True)
            sel.register(proc.stdout, selectors.EVENT_READ)
            while True:
                elapsed = time.monotonic() - started
                used = size(args.output)
                if cancelled[0]:
                    forced = 'cancelled'
                elif elapsed >= min(defaults['case_timeout_seconds'], remaining):
                    forced = 'timeout'
                elif used >= defaults['max_output_bytes']:
                    forced = 'output_limit'
                elif shutil.disk_usage(args.output).free < defaults['min_free_disk_bytes']:
                    forced = 'disk_limit'
                if forced:
                    break
                for key, _ in sel.select(.05):
                    data = os.read(key.fd, 65536)
                    if data:
                        allowance = max(0, defaults['max_output_bytes'] - used)
                        out.write(data[:allowance])
                        out.flush()
                        if len(data) > allowance:
                            forced = 'output_limit'
                    else:
                        sel.unregister(key.fileobj)
                if forced or (proc.poll() is not None and not sel.get_map()):
                    break
        except OSError as error:
            report['launch_error'] = str(error)
            forced = 'process_failed'
        finally:
            if proc:
                stop_group(proc)
                proc.stdout.close()
    code = proc.returncode if proc else None
    # Tail bounds memory even when output quota is large; summary is emitted last.
    with log.open('rb') as src:
        length = log.stat().st_size
        if length > 8 * 1024 * 1024:
            head = src.read(1024 * 1024)
            src.seek(length - 7 * 1024 * 1024)
            data = head + b'\n[experiment] middle of log omitted from parser\n' + src.read()
        else:
            data = src.read()
        parsed = parse_log(data.decode('utf-8', 'replace'), spec['environment']['PS2_GS'], defaults['frames'], code)
        report['log_parser_truncated'] = length > 8 * 1024 * 1024
    report.update(parsed)
    if forced:
        report['status'] = forced
    elif size(args.output) >= defaults['max_output_bytes']:
        report['status'] = 'output_limit'
    elif shutil.disk_usage(args.output).free < defaults['min_free_disk_bytes']:
        report['status'] = 'disk_limit'
    report.update(end=now(), wall_seconds=time.monotonic() - started, exit_code=code,
                  signal=-code if code is not None and code < 0 else None,
                  budget_limited=remaining <= defaults['case_timeout_seconds'])
    report['artifacts'] = inventory(directory)
    report['output_bytes'] = sum(f['bytes'] for f in report['artifacts'].values())
    report['frame_hashes'] = {p: f['sha256'] for p, f in report['artifacts'].items() if p.startswith('frames/')}
    last = report['last_guest_frame'] or 0
    expected = set(range(defaults['frame_every'], last + 1, defaults['frame_every']))
    expected.add(last)  # Runtime dumps on halt, including early halt.
    present = {int(Path(p).stem.split('_')[-1]) for p in report['frame_hashes'] if re.fullmatch(r'frames/frame_\d+\.ppm', p)}
    report['missing_captures'] = sorted(expected - present)
    report['sealed'] = report['status'] != 'cancelled'
    atomic(directory / 'case.json', report)
    return report


def ppm(path):
    if path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError('PPM exceeds native 2048x2048 image bound')
    data = path.read_bytes()
    header = re.match(rb'P6\s+(\d+)\s+(\d+)\s+255\s', data)
    if not header:
        raise ValueError('unsupported PPM header')
    w, h = map(int, header.groups())
    pixels = data[header.end():]
    if len(pixels) != w * h * 3:
        raise ValueError('truncated PPM')
    return (w, h), pixels


def compare(a, b, output):
    common = sorted(set(a['frame_hashes']) & set(b['frame_hashes']))
    result = {'a': a['id'], 'b': b['id'], 'a_directory': a['directory'], 'b_directory': b['directory'],
              'compared_frames': len(common),
              'missing_in_a': sorted(set(b['frame_hashes']) - set(a['frame_hashes'])),
              'missing_in_b': sorted(set(a['frame_hashes']) - set(b['frame_hashes'])),
              'first_divergence': None, 'pixel_mismatch_count': 0, 'max_channel_delta': 0,
              'comparison_errors': [], 'reliable': a['status'] == b['status'] == 'frame_limit_reached'
              and not a['missing_captures'] and not b['missing_captures'] and bool(common),
              'outcome_equal': all(a.get(k) == b.get(k) for k in
                                   ('status', 'halt_reason', 'last_guest_frame', 'last_guest_cycle'))}
    for frame in common:
        if a['frame_hashes'][frame] != b['frame_hashes'][frame] and result['first_divergence'] is None:
            result['first_divergence'] = frame
        try:
            dimensions, x = ppm(output / a['directory'] / frame)
            dims_b, y = ppm(output / b['directory'] / frame)
            if dimensions != dims_b:
                raise ValueError('different image dimensions')
            count, delta = 0, 0
            if x != y:
                for i in range(0, len(x), 3):
                    if x[i:i+3] != y[i:i+3]:
                        count += 1
                        delta = max(delta, *(abs(x[j] - y[j]) for j in range(i, i+3)))
            result['pixel_mismatch_count'] += count
            result['max_channel_delta'] = max(result['max_channel_delta'], delta)
            if count and result['first_divergence'] is None:
                result['first_divergence'] = frame
        except (OSError, ValueError) as error:
            result['comparison_errors'].append({'frame': frame, 'error': str(error)})
            result['reliable'] = False
    if result['missing_in_a'] or result['missing_in_b']:
        result['reliable'] = False
    return result


def save_run(args, report):
    latest = {r['id']: r for r in report['results']}
    values = list(latest.values())
    repeat, cross = [], []
    cached = {(c['a_directory'], c['b_directory']): c
              for group in report.get('comparisons', {}).values() for c in group}

    def comparison(a, b):
        key = (a['directory'], b['directory'])
        return cached[key] if key in cached else compare(a, b, args.output)

    for i, a in enumerate(values):
        for b in values[i+1:]:
            if a['scenario'] != b['scenario']:
                continue
            if a['variant'] == b['variant']:
                item = comparison(a, b)
                item['repeatable'] = (item['reliable'] and item['outcome_equal']
                                      and item['first_divergence'] is None
                                      and a['observed_backend'] == b['observed_backend'])
                repeat.append(item)
            elif a['repetition'] == b['repetition'] == 1:
                cross.append(comparison(a, b))
    for comparison in cross:
        evidence = []
        for case_id in (comparison['a'], comparison['b']):
            case = latest[case_id]
            matches = [r['repeatable'] for r in repeat
                       if latest[r['a']]['scenario'] == case['scenario']
                       and latest[r['a']]['variant'] == case['variant']]
            evidence.append(all(matches) if matches else None)
        comparison['repeatability_established'] = (False if False in evidence else
                                                  None if None in evidence else True)
    report['comparisons'] = {'repeatability': repeat, 'cross_variant': cross}
    report['pending'] = [c['id'] for c in report['cases'] if c['id'] not in latest or not latest[c['id']]['sealed']]
    report['updated'] = now()
    atomic(args.output / 'report.json', report)
    lines = [f"# {report['name']}", f"Source: {report['identity']['source_commit']}",
             f"Dirty source: {report['identity']['source_dirty']}",
             f"Run state: {report['state']}; pending: {len(report['pending'])}",
             'Gameplay verified: false. Pixel equality does not establish visual correctness or compatibility.',
             '', '| Case | Result | Backend | Frame | Missing captures |', '| --- | --- | --- | --- | --- |']
    for r in values:
        lines.append(f"| {r['id']} | {r['status']} | {r['observed_backend']} | {r['last_guest_frame']} | {len(r['missing_captures'])} |")
    for label, comparisons in [('Repeatability', repeat), ('Cross variant', cross)]:
        for c in comparisons:
            lines.append(f"\n{label}: {c['a']} / {c['b']}: {c['compared_frames']} frames; "
                         f"first divergence {c['first_divergence']}; {c['pixel_mismatch_count']} differing pixels; "
                         f"max channel delta {c['max_channel_delta']}; reliable full comparison: {c['reliable']}; "
                         f"same runtime outcome: {c['outcome_equal']}; missing captures {len(c['missing_in_a'])}/{len(c['missing_in_b'])}.")
            if label == 'Repeatability':
                lines.append(f"Repeatable full case: {c['repeatable']}.")
            else:
                lines.append(f"Repeatability established for both variants: {c['repeatability_established']}. "
                             'Pixel differences are observations, not a correctness verdict.')
    missing = {}
    for r in values:
        if r['first_missing_pc']:
            key = f"{r['first_missing_pc']} / {r['first_missing_ra']}"
            missing[key] = missing.get(key, 0) + 1
    lines.append('\nMissing PC / RA groups: ' + json.dumps(missing))
    # No home directory paths or raw runtime reasons in the shareable summary.
    atomic(args.output / 'summary.md', ('\n'.join(lines) + '\n').replace(str(Path.home()), '~'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('manifest', 'iso', 'runner', 'elf', 'generated', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--pilot', action='store_true', help='only the documented three boot-idle cases')
    args = parser.parse_args(argv)
    for name in ('manifest', 'iso', 'runner', 'elf', 'generated'):
        setattr(args, name, getattr(args, name).expanduser().resolve(strict=True))
    args.output = args.output.expanduser().resolve()
    local = ROOT / 'local/experiments'
    if not args.output.is_relative_to(local.resolve()) or args.output == local.resolve():
        parser.error('--output must be a run directory under ignored local/experiments/')
    m = manifest_read(args.manifest)
    plan = cases(m, args.pilot)
    defaults = m['defaults']
    if not args.generated.is_dir() or not all(p.is_file() for p in (args.runner, args.elf, args.iso)):
        raise ValueError('runner, ELF and ISO must be files; generated must be a directory')
    if args.generated.is_relative_to(args.output) or args.output.is_relative_to(args.generated):
        raise ValueError('generated code and output must be separate')
    cancelled = [False]
    old_handlers = {}
    for sig in (signal.SIGINT, signal.SIGTERM):
        old_handlers[sig] = signal.signal(sig, lambda *_: cancelled.__setitem__(0, True))
    enable_subreaper()
    try:
        with ExitStack() as stack:
            # Locks live outside inventories; build parent serializes binaries sharing a build.
            for resource in sorted({str(args.runner.parent), str(args.generated), str(args.output)}):
                stack.enter_context(lock(local / '.locks' / (digest(resource.encode()) + '.lock')))
            if args.resume:
                report = json.loads((args.output / 'report.json').read_text())
            else:
                args.output.mkdir(parents=True, exist_ok=False)
                report = None
            print('Fingerprinting source, binary, generated code, ELF, manifest and ISO...', flush=True)
            identity = identities(args)
            if report:
                if report['identity'] != identity or report['cases'] != plan:
                    raise ValueError('resume identity or case selection mismatch; start a new run')
                if sha(args.output / 'manifest.json') != identity['manifest_sha256']:
                    raise ValueError('resume manifest snapshot mismatch')
                for r in report['results']:
                    directory = args.output / r['directory']
                    if json.loads((directory / 'case.json').read_text()) != r:
                        raise ValueError('resume case report mismatch: ' + r['id'])
                    actual = inventory(directory)
                    actual.pop('case.json', None)
                    if actual != r['artifacts']:
                        raise ValueError('resume artifact mismatch: ' + r['id'])
                # Derive metrics anew from validated artifacts on resume rather
                # than trusting cached presentation data in the run report.
                report['comparisons'] = {}
            else:
                (args.output / 'manifest.json').write_bytes(args.manifest.read_bytes())
                report = {'schema_version': 1, 'name': m['name'], 'identity': identity,
                          'metadata': metadata(args), 'cases': plan, 'results': [], 'elapsed_seconds': 0,
                          'started': now(), 'gameplay_verified': False}
            started = time.monotonic()
            consumed = report['elapsed_seconds']
            report['state'] = 'running'
            save_run(args, report)
            for spec in plan:
                previous = next((r for r in reversed(report['results']) if r['id'] == spec['id']), None)
                if previous and previous['sealed']:
                    continue
                remaining = defaults['total_timeout_seconds'] - consumed - (time.monotonic() - started)
                stop = ('cancelled' if cancelled[0] else 'total_timeout' if remaining <= 0 else
                        'output_limit' if size(args.output) >= defaults['max_output_bytes'] else
                        'disk_limit' if shutil.disk_usage(args.output).free < defaults['min_free_disk_bytes'] else None)
                if stop:
                    report['state'] = stop
                    break
                print('Running ' + spec['id'], flush=True)
                result = execute(args, spec, defaults, cancelled, remaining)
                report['results'].append(result)
                report['elapsed_seconds'] = consumed + time.monotonic() - started
                save_run(args, report)
                print(spec['id'] + ': ' + result['status'], flush=True)
                if result['status'] in ('cancelled', 'output_limit', 'disk_limit'):
                    report['state'] = result['status']
                    break
            else:
                report['state'] = 'finished'
            report['elapsed_seconds'] = consumed + time.monotonic() - started
            save_run(args, report)
            print('Report: ' + str(args.output / 'summary.md'), flush=True)
            return 130 if cancelled[0] else 0
    finally:
        for sig, handler in old_handlers.items():
            signal.signal(sig, handler)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError, TypeError) as error:
        print('error: ' + str(error), file=sys.stderr)
        sys.exit(2)
