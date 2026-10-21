"""Original fake-subprocess checks for the offline prefix wrapper; no game data."""
import contextlib
import io
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import unittest
from unittest import mock

import run_vu_prefix as wrapper

FAKE = '''#!/usr/bin/env python3
import json,os,pathlib,sys,time
assert not any(k.startswith('PS2_') for k in os.environ)
mode=sys.argv[2];out=pathlib.Path(sys.argv[3]);test=os.environ.get('VU_TEST_MODE')
if test=='timeout':time.sleep(60)
for suffix in ('regs.bin','mem.bin','packets.bin','pipe.txt'):
 value=b'synthetic'
 if test=='mismatch' and mode.startswith('interpreted') and suffix=='regs.bin':value=b'different'
 pathlib.Path(str(out)+'-'+suffix).write_bytes(value)
status=dict(complete=False,reason='continuation_limit' if mode.startswith('compiled') else 'instruction_checkpoint',
 next_pc=16,issue_clock_delta=4,continuations=8192 if mode.startswith('compiled') else 0,
 steps=0 if mode.startswith('compiled') else 4,npc=24,ending=False)
pathlib.Path(str(out)+'-status.json').write_text('invalid' if test=='malformed' else json.dumps(status))
sys.exit(4)
'''


class PrefixWrapper(unittest.TestCase):
    def setUp(self):
        parent = wrapper.ROOT/'local/experiments'
        parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='prefix-test-', dir=parent)
        self.root = Path(self.temp.name)
        self.snapshot = self.root/'input'
        for suffix in ('code.bin', 'before.bin', 'memory.bin', 'meta.txt', 'pipe.bin'):
            Path(str(self.snapshot)+'-'+suffix).write_bytes(b'original synthetic input')
        self.runner = self.root/'fake.py'
        self.runner.write_text(FAKE)
        self.runner.chmod(0o700)
        self.generated = self.root/'generated'
        self.generated.mkdir()
        (self.generated/'synthetic.cpp').write_text('// Original synthetic fixture\n')
        self.output = self.root/'result'

    def tearDown(self):
        self.temp.cleanup()

    def invoke(self, mode='', seconds=3):
        argv = ['run_vu_prefix.py', '--snapshot', str(self.snapshot), '--runner', str(self.runner),
                '--generated', str(self.generated), '--output', str(self.output)]
        handlers = {s: signal.getsignal(s) for s in (signal.SIGTERM, signal.SIGINT)}
        try:
            with mock.patch.object(sys, 'argv', argv), mock.patch.object(wrapper, 'CASE_SECONDS', seconds), \
                 mock.patch.object(wrapper, 'MIN_FREE', 0), \
                 mock.patch.dict(os.environ, {'VU_TEST_MODE': mode, 'PS2_VU_INTERPRET': '1'}), \
                 contextlib.redirect_stdout(io.StringIO()):
                return wrapper.main()
        finally:
            for sig, handler in handlers.items():
                signal.signal(sig, handler)

    def report(self):
        return json.loads((self.output/'report.json').read_text())

    def test_prefix_is_partial_and_aligned(self):
        self.assertEqual(self.invoke(), 0)
        report = self.report()
        self.assertEqual([c['outcome'] for c in report['cases']], ['partial_checkpoint']*2)
        self.assertFalse(report['comparison']['full_invocation_compared'])
        self.assertTrue(all(report['comparison']['exact_fields'].values()))
        self.assertEqual(report['cases'][1]['argv'][-1], '4')

    def test_mismatch_stays_visible_and_fails(self):
        self.assertEqual(self.invoke('mismatch'), 1)
        self.assertFalse(self.report()['comparison']['exact_fields']['regs.bin'])

    def test_timeout_stops_before_second_case(self):
        self.assertEqual(self.invoke('timeout', seconds=.1), 1)
        report = self.report()
        self.assertEqual(len(report['cases']), 1)
        self.assertEqual(report['cases'][0]['outcome'], 'timeout')
        self.assertNotEqual(report['cases'][0]['exit_code'], 0)
        self.assertIsNone(report['comparison'])

    def test_malformed_status_is_not_agreement(self):
        self.assertEqual(self.invoke('malformed'), 1)
        self.assertEqual(self.report()['cases'][0]['outcome'], 'process_failed')
        self.assertIsNone(self.report()['comparison'])

    def test_existing_output_is_not_reused(self):
        self.output.mkdir()
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.invoke()


if __name__ == '__main__':
    unittest.main()
