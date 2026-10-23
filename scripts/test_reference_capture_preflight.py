import configparser
from pathlib import Path
import tempfile
import unittest
import struct
import zlib

from reference_capture_preflight import check, framebuffer_images


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

    def test_png_output_satisfies_early_output_check(self):
        def chunk(name, data):
            return struct.pack('>I', len(data))+name+data+struct.pack('>I', zlib.crc32(name+data))
        png = (b'\x89PNG\r\n\x1a\n'
               + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
               + chunk(b'IDAT', zlib.compress(b'\0\xff\0\0')) + chunk(b'IEND', b''))
        path = self.root/'frame.png'
        path.write_bytes(png)
        (self.root/'partial.png').write_bytes(png[:-12])
        (self.root/'not-an-image.bmp').write_text('a diagnostic message')
        self.assertEqual(framebuffer_images(self.root), [path])

    def test_bmp_output_remains_recognized(self):
        bmp = (b'BM'+struct.pack('<IHHI', 58, 0, 0, 54)
               + struct.pack('<IiiHHIIiiII', 40, 1, 1, 1, 24, 0, 4, 0, 0, 0, 0)
               + b'\0\0\xff\0')
        path = self.root/'frame.bmp'
        path.write_bytes(bmp)
        self.assertEqual(framebuffer_images(self.root), [path])


if __name__ == '__main__':
    unittest.main()
