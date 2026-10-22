import configparser
from pathlib import Path
import tempfile
import unittest

from reference_capture_preflight import check


class CapturePreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.config = configparser.ConfigParser(interpolation=None)
        self.config.optionxform = str
        self.config.read_dict({'EmuCore/GS': {
            'DumpGSData': 'true', 'SaveFrame': 'true',
            'HWDumpDirectory': str(self.root), 'SWDumpDirectory': str(self.root),
            'SaveFrameCount': '2400', 'SaveFrameBy': '15', 'SaveDrawCount': '-1',
        }, 'UI': {'StartPaused': 'false'}})

    def test_complete_configuration(self):
        self.assertEqual(check(self.config, self.root), [])

    def test_missing_unused_software_directory_blocks_hardware_capture(self):
        self.config['EmuCore/GS']['SWDumpDirectory'] = ''
        self.assertTrue(any('SWDumpDirectory' in e for e in check(self.config, self.root)))

    def test_escaped_directory_and_unbounded_range_fail(self):
        self.config['EmuCore/GS']['HWDumpDirectory'] = str(self.root.parent)
        self.config['EmuCore/GS']['SaveFrameCount'] = '-1'
        errors = check(self.config, self.root)
        self.assertTrue(any('HWDumpDirectory' in e for e in errors))
        self.assertTrue(any('finite' in e for e in errors))


if __name__ == '__main__':
    unittest.main()
