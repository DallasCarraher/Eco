"""Original synthetic subprocess tests; no game data, network, or build required."""
import copy
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

import run_experiments as runner

ROOT = runner.ROOT
FAKE = r'''
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
MODE = __MODE__
a = sys.argv
out = Path(a[a.index('--frames-dir')+1])
card = Path(a[a.index('--memcard')+1])
assert not card.exists()
assert not any(k.startswith('PS2_') and k not in {'PS2_WINDOW_FULL', 'PS2_GS', 'PS2_VU_INTERPRET', 'PS2_GS_COMPARE', 'PS2_VU_CHECK', 'PS2_VU_CHECK_CONTINUATIONS'} for k in os.environ)
assert os.environ['PS2_WINDOW_FULL'] == '1'
card.write_bytes(b'fresh synthetic card')
Path('settings.json').write_text(__import__('json').dumps({k:v for k,v in os.environ.items() if k.startswith('PS2_')}))
if MODE == 'closed-child':
    child = subprocess.Popen([sys.executable, '-c', 'import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    Path('child.pid').write_text(str(child.pid))
    time.sleep(.08)
if MODE in ('sleep', 'orphan', 'quota'):
    child = subprocess.Popen([sys.executable, '-c', 'import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)'])
    Path('child.pid').write_text(str(child.pid))
    time.sleep(.08)
    if MODE == 'orphan':
        sys.exit(0)
    if MODE == 'quota':
        Path('flood.bin').write_bytes(b'x' * 65536)
    while True:
        time.sleep(.01)
if MODE == 'log-quota':
    while True:
        os.write(1, b'x' * 65536)
if MODE == 'failure':
    sys.exit(7)
if MODE == 'missing':
    sys.exit(0)
f = int(a[a.index('--frames')+1])
if MODE != 'no-captures':
    for n in range(1, f+1):
        pixel = b'\x01\x02\x03' if os.environ['PS2_GS'] == 'cpu' else b'\x01\x02\x04'
        (out / ('frame_%05d.ppm' % n)).write_bytes(b'P6\n1 1\n255\n' + pixel)
if os.environ['PS2_GS'] != 'cpu':
    if MODE == 'fallback':
        print('[gpu] Apple Synthetic ()')
        print('[gs] WebGPU unavailable, using the software renderer')
    elif MODE != 'unknown-gpu':
        print('[gpu] Apple Synthetic ()')
        print('[gpu] 10 submits, dispatches: test 10')
reason = 'missing code at 0x00689DA0 (ra 0x0068964C)' if MODE == 'halt' else 'frame limit reached'
print('[ee] halted: ' + reason)
print('[ee] stopped after %d frames, 123 cycles: %s' % (f, reason))
if MODE == 'malformed':
    print('[ee] stopped after nonsense')
    print('[ee] stopped after 1 frames, 1 cycles: inconsistent')
'''


class Experiments(unittest.TestCase):
    def setUp(self):
        (ROOT / 'local/experiments').mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix='runner fixture with spaces ', dir=ROOT / 'local/experiments')
        self.base = Path(self.tmp.name)
        self.output = self.base / 'output with spaces'
        self.binary = self.base / 'native with spaces'
        self.generated = self.base / 'generated with spaces'
        self.generated.mkdir()
        (self.generated / 'unit.cpp').write_text('// synthetic\n')
        self.iso = self.base / 'disc with spaces.iso'
        self.elf = self.base / 'elf with spaces'
        self.iso.write_bytes(b'original synthetic disc')
        self.elf.write_bytes(b'original synthetic elf')
        self.manifest = self.base / 'manifest with spaces.json'
        self.m = {'schema_version': 1, 'name': 'synthetic', 'defaults': {
            'frames': 2, 'frame_every': 1, 'repetitions': 2, 'case_timeout_seconds': 2,
            'total_timeout_seconds': 30, 'max_output_bytes': 2000000, 'min_free_disk_bytes': 1,
            'concurrency': 1, 'initial_memory_card': 'fresh_per_case',
            'environment': {'PS2_WINDOW_FULL': '1'}},
            'scenarios': [{'id': 'boot-idle', 'presses': []}],
            'variants': [{'id': 'gpu-compiled', 'environment': {'PS2_GS': 'gpu'}},
                         {'id': 'cpu-compiled', 'environment': {'PS2_GS': 'cpu'}}]}
        self.fake('normal')

    def tearDown(self):
        self.tmp.cleanup()

    def fake(self, mode):
        self.binary.write_text('#!' + sys.executable + '\n' + FAKE.replace('__MODE__', repr(mode)))
        self.binary.chmod(0o755)

    def command(self, resume=False, pilot=False):
        self.manifest.write_text(json.dumps(self.m))
        cmd = [sys.executable, str(ROOT / 'scripts/run_experiments.py'),
               '--manifest', str(self.manifest), '--iso', str(self.iso), '--elf', str(self.elf),
               '--runner', str(self.binary), '--generated', str(self.generated), '--output', str(self.output)]
        return cmd + (['--resume'] if resume else []) + (['--pilot'] if pilot else [])

    def run_batch(self, resume=False, pilot=False, expected=0):
        env = dict(os.environ, PS2_DUMP='inherited bad path', PS2_GS='both', PS2_VU_CHECK='1')
        p = subprocess.run(self.command(resume, pilot), env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, expected, p.stdout + p.stderr)
        return json.loads((self.output / 'report.json').read_text()) if expected == 0 else p

    def one(self, mode, status):
        self.fake(mode)
        self.m['defaults']['repetitions'] = 1
        self.m['variants'] = [{'id': 'cpu-compiled', 'environment': {'PS2_GS': 'cpu'}}]
        report = self.run_batch()
        self.assertEqual(report['results'][0]['status'], status)
        return report

    def assert_child_dead(self, report):
        for case in report['results']:
            pid = int((self.output / case['directory'] / 'child.pid').read_text())
            # macOS launchd may briefly retain an orphan zombie; it cannot execute.
            state = subprocess.run(['ps', '-p', str(pid), '-o', 'stat='], capture_output=True, text=True).stdout.strip()
            self.assertTrue(not state or state.startswith('Z'), (pid, state))

    def test_frame_limit_pilot_environment_paths_and_repeatability(self):
        r = self.run_batch(pilot=True)
        self.assertEqual(len(r['results']), 3)
        self.assertEqual([x['repetition'] for x in r['results']], [1, 2, 1])
        self.assertTrue(all(x['status'] == 'frame_limit_reached' for x in r['results']))
        repeat = r['comparisons']['repeatability'][0]
        self.assertTrue(repeat['reliable'])
        self.assertTrue(repeat['repeatable'])
        self.assertIsNone(repeat['first_divergence'])
        cross = r['comparisons']['cross_variant'][0]
        self.assertEqual(cross['first_divergence'], 'frames/frame_00001.ppm')
        self.assertEqual(cross['pixel_mismatch_count'], 2)
        self.assertEqual(cross['max_channel_delta'], 1)
        self.assertIsNone(cross['repeatability_established'])
        self.assertEqual(r['results'][0]['observed_backend'], 'gpu')
        self.assertEqual(r['results'][2]['observed_backend'], 'cpu')

    def test_zero_exit_halt(self):
        r = self.one('halt', 'runtime_halted')['results'][0]
        self.assertEqual(r['exit_code'], 0)
        self.assertEqual(r['first_missing_pc'], '0x00689DA0')

    def test_missing_summary(self):
        self.one('missing', 'incomplete')

    def test_malformed_summary(self):
        self.one('malformed', 'incomplete')

    def test_process_failure(self):
        self.one('failure', 'process_failed')

    def test_missing_captures_are_not_equality(self):
        self.fake('no-captures')
        r = self.run_batch()
        self.assertEqual(r['results'][0]['missing_captures'], [1, 2])
        self.assertFalse(r['comparisons']['repeatability'][0]['reliable'])

    def test_software_fallback_and_unknown_gpu(self):
        for mode in ('fallback', 'unknown-gpu'):
            with self.subTest(mode=mode):
                self.output = self.base / mode
                self.fake(mode)
                r = self.run_batch()
                self.assertEqual(r['results'][0]['status'], 'unsupported')
                self.assertEqual(r['results'][0]['observed_backend'], 'cpu' if mode == 'fallback' else 'unknown')

    def test_timeout_child_and_exited_parent(self):
        for mode in ('sleep', 'orphan'):
            with self.subTest(mode=mode):
                self.output = self.base / mode
                r = self.one(mode, 'timeout')
                self.assert_child_dead(r)

    def test_success_still_cleans_detached_pipes_child(self):
        r = self.one('closed-child', 'frame_limit_reached')
        self.assert_child_dead(r)

    def test_quotas_and_child_cleanup(self):
        self.m['defaults']['max_output_bytes'] = 20000
        r = self.one('quota', 'output_limit')
        self.assert_child_dead(r)
        self.assertEqual(len(r['pending']), 0)

    def test_streamed_log_quota(self):
        self.m['defaults']['max_output_bytes'] = 20000
        r = self.one('log-quota', 'output_limit')
        self.assertLessEqual((self.output / r['results'][0]['directory'] / 'runtime.log').stat().st_size, 20000)

    def test_disk_preflight(self):
        self.m['defaults']['min_free_disk_bytes'] = 10**18
        r = self.run_batch()
        self.assertEqual(r['state'], 'disk_limit')
        self.assertFalse(r['results'])
        self.assertEqual(len(r['pending']), 4)

    def test_disk_limit_during_case(self):
        self.fake('sleep')
        self.output.mkdir()
        spec = runner.cases(self.m)[0]
        args = argparse.Namespace(output=self.output, runner=self.binary, iso=self.iso, elf=self.elf)
        with mock.patch.object(runner.shutil, 'disk_usage', return_value=argparse.Namespace(free=0)):
            r = runner.execute(args, spec, self.m['defaults'], [False], 30)
        self.assertEqual(r['status'], 'disk_limit')
        self.assertIsNotNone(r['exit_code'])

    def test_press_argv(self):
        self.m['scenarios'] = [{'id': 'boot-start', 'presses': ['1:start:2']}]
        r = self.run_batch()
        argv = r['results'][0]['argv']
        self.assertEqual(argv[argv.index('--press') + 1], '1:start:2')

    def test_total_budget_pending(self):
        self.fake('sleep')
        self.m['defaults']['total_timeout_seconds'] = 1
        r = self.run_batch()
        self.assertEqual(r['state'], 'total_timeout')
        self.assertEqual(len(r['results']), 1)
        self.assertEqual(len(r['pending']), 3)
        self.assert_child_dead(r)

    def test_cancellation_child_cleanup_and_resume_new_directory(self):
        self.fake('sleep')
        p = subprocess.Popen(self.command(), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            until = time.monotonic() + 10
            while not list(self.output.glob('*/child.pid')) and time.monotonic() < until:
                time.sleep(.02)
            self.assertTrue(list(self.output.glob('*/child.pid')))
            time.sleep(.15)
            p.send_signal(signal.SIGTERM)
            _, error = p.communicate(timeout=10)
            self.assertEqual(p.returncode, 130, error)
        finally:
            if p.poll() is None:
                p.kill()
                p.wait()
            p.stderr.close()
        r = json.loads((self.output / 'report.json').read_text())
        self.assertEqual(r['state'], 'cancelled')
        self.assertEqual(r['results'][0]['status'], 'cancelled')
        self.assertEqual(len(r['pending']), 4)
        self.assert_child_dead(r)
        # Resume unchanged binary, give its next attempt a short bounded timeout.
        p = subprocess.Popen(self.command(resume=True), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            until = time.monotonic() + 10
            while len(list(self.output.glob('*/child.pid'))) < 2 and time.monotonic() < until:
                time.sleep(.02)
            p.send_signal(signal.SIGINT)
            p.communicate(timeout=10)
        finally:
            if p.poll() is None:
                p.kill()
                p.wait()
            p.stderr.close()
        r = json.loads((self.output / 'report.json').read_text())
        self.assertEqual(len(r['results']), 2)
        self.assertNotEqual(r['results'][0]['directory'], r['results'][1]['directory'])
        self.assert_child_dead(r)

    def test_lock_contention_build_generated_and_output(self):
        for resource in (self.binary.parent, self.generated, self.output):
            with self.subTest(resource=resource):
                path = ROOT / 'local/experiments/.locks' / (runner.digest(str(resource).encode()) + '.lock')
                with runner.lock(path):
                    p = self.run_batch(expected=2)
                    self.assertIn('resource locked', p.stderr)

    def test_resume_skips_and_checks_input_hashes(self):
        first = self.run_batch()
        resumed = self.run_batch(resume=True)
        self.assertEqual(first['results'], resumed['results'])
        for path in (self.binary, self.elf, self.iso, self.generated / 'unit.cpp'):
            with self.subTest(path=path):
                original = path.read_bytes()
                path.write_bytes(original + b'changed')
                p = self.run_batch(resume=True, expected=2)
                self.assertIn('identity', p.stderr)
                path.write_bytes(original)
        self.m['defaults']['frames'] = 3
        self.assertIn('identity', self.run_batch(resume=True, expected=2).stderr)

    def test_resume_validates_artifacts_and_case_reports(self):
        r = self.run_batch()
        directory = self.output / r['results'][0]['directory']
        log = directory / 'runtime.log'
        original = log.read_bytes()
        log.write_bytes(b'corrupted')
        self.assertIn('artifact mismatch', self.run_batch(resume=True, expected=2).stderr)
        log.write_bytes(original)
        (directory / 'case.json').write_text('{}')
        self.assertIn('case report mismatch', self.run_batch(resume=True, expected=2).stderr)

    def test_chain_diagnostic_counts_and_setting(self):
        self.m['variants'][0]['environment']['PS2_VU_CHECK'] = 'all'
        self.manifest.write_text(json.dumps(self.m))
        runner.manifest_read(self.manifest)
        log = '[vu-chain-summary] compared 12 chains, 30 continuations, 2 interpreter fallbacks, 7 mismatches, 3 nonflag\n'
        parsed = runner.parse_log(log, 'cpu', 510, 0)
        self.assertEqual(parsed['chain_comparison_counts'], dict(chains=12, continuations=30,
                         interpreter_fallbacks=2, mismatches=7, nonflag=3))
        self.assertIsNone(parsed['comparison_counts']['checked_final'])
        self.assertIsNone(runner.parse_log(log, 'cpu', 510, 1)['chain_comparison_counts'])
        self.m['variants'][0]['environment']['PS2_VU_CHECK'] = 'unbounded'
        self.manifest.write_text(json.dumps(self.m))
        with self.assertRaises(ValueError):
            runner.manifest_read(self.manifest)

    def test_bounded_chain_outcomes(self):
        complete = '[vu-chain-outcomes] attempted 2 complete 2 mismatch 0 budget_exhausted 0 unsupported 0 unchecked_tail_dispatches 0 checkpoints 40 continuations 10000\n'
        parsed = runner.parse_log(complete, 'cpu', 510, 0)
        self.assertTrue(parsed['chain_comparison_complete_for_attempted'])
        self.assertEqual(parsed['chain_comparison_outcomes']['complete_match'], 2)
        self.assertIsNone(parsed['chain_comparison_counts'])
        for label, counts in [('mismatch', '0 1 0 0'), ('budget', '0 0 1 0'), ('unsupported', '0 0 0 1')]:
            a, b, c, d = counts.split()
            log = f'[vu-chain-outcomes] attempted 1 complete {a} mismatch {b} budget_exhausted {c} unsupported {d} unchecked_tail_dispatches 3 checkpoints 32 continuations 8192\n'
            self.assertFalse(runner.parse_log(log, 'cpu', 510, 0)['chain_comparison_complete_for_attempted'], label)
        for log, code in [(complete, 1), (complete+complete, 0), ('', 0), (complete.replace('attempted 2', 'attempted 3'), 0)]:
            self.assertIsNone(runner.parse_log(log, 'cpu', 510, code)['chain_comparison_outcomes'])

    def test_malformed_chain_outcome_markers(self):
        complete = '[vu-chain-outcomes] attempted 1 complete 1 mismatch 0 budget_exhausted 0 unsupported 0 unchecked_tail_dispatches 0 checkpoints 1 continuations 0\n'
        for malformed in ('[vu-chain-outcomes] attempted 1 complete 0 mismatch 1',
                          '[vu-chain-outcomes]',
                          complete.rstrip() + ' trailing text'):
            for log in (malformed, complete + malformed, malformed + '\n' + complete):
                with self.subTest(log=log):
                    parsed = runner.parse_log(log, 'cpu', 510, 0)
                    self.assertIsNone(parsed['chain_comparison_outcomes'])
                    self.assertIsNone(parsed['chain_comparison_complete_for_attempted'])

    def test_explicit_chain_policy_setting(self):
        env = self.m['variants'][0]['environment']
        env['PS2_VU_CHECK'] = 'all'
        for value in ('8192', '16384'):
            env['PS2_VU_CHECK_CONTINUATIONS'] = value
            self.manifest.write_text(json.dumps(self.m))
            runner.manifest_read(self.manifest)
        report = self.run_batch()
        case = report['results'][0]
        settings = json.loads((self.output/case['directory']/'settings.json').read_text())
        self.assertEqual(settings['PS2_VU_CHECK_CONTINUATIONS'], '16384')
        for value in ('32768', 'unlimited', 16384):
            env['PS2_VU_CHECK_CONTINUATIONS'] = value
            self.manifest.write_text(json.dumps(self.m))
            with self.assertRaises(ValueError): runner.manifest_read(self.manifest)
        env['PS2_VU_CHECK_CONTINUATIONS'] = '16384'
        env['PS2_VU_CHECK'] = '1'
        self.manifest.write_text(json.dumps(self.m))
        with self.assertRaises(ValueError): runner.manifest_read(self.manifest)

    def test_manifest_validation(self):
        original = copy.deepcopy(self.m)
        for edit in (lambda m: m['defaults'].update(frames=True),
                     lambda m: m['defaults'].update(concurrency=2),
                     lambda m: m['variants'][0]['environment'].update(PS2_DUMP='bad'),
                     lambda m: m['scenarios'][0].update(presses=['0:start:2']),
                     lambda m: m['variants'][0].update(id='../escape')):
            self.m = copy.deepcopy(original)
            edit(self.m)
            self.manifest.write_text(json.dumps(self.m))
            with self.assertRaises(ValueError):
                runner.manifest_read(self.manifest)


if __name__ == '__main__':
    (ROOT / 'local/experiments').mkdir(parents=True, exist_ok=True)
    unittest.main()
