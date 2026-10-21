"""Regression checks for selecting heap snapshots without capturing boot code."""
import contextlib
import io
from pathlib import Path
import struct
import tempfile
import unittest

from heap_windows import RAM_SIZE, capture, goal_function_entries
from goal_toplevels import templates


class HeapCaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.misses = self.root / 'misses.txt'
        self.out = self.root / 'overlays'
        self.ram = bytearray(RAM_SIZE)
        self.ram[0x180008:0x18000c] = b'\x04\x00\x03\x24'
        header = bytearray(52)
        struct.pack_into('<I', header, 28, 52)
        struct.pack_into('<HH', header, 42, 32, 1)
        self.elf = header + struct.pack('<8I', 1, 0x100, 0x100000,
                                        0x100000, 16, 0x4000, 5, 16)

    def run_capture(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return capture(self.elf, self.ram, self.out, self.misses)

    def test_observed_heap_entry_gets_snapshot_and_module_token(self):
        self.misses.write_text('180008\n')
        self.assertEqual(self.run_capture(), 1)
        files = list(self.out.glob('*.bin'))
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].read_bytes(), self.ram[0x180000:0x188000])
        self.assertEqual(self.misses.read_text(), files[0].stem + ':8\n')
        # Re-observing the same page must reuse the snapshot.
        self.misses.write_text('180008\n')
        self.run_capture()
        self.assertEqual(list(self.out.glob('*.bin')), files)

    def test_boot_segments_unaligned_low_and_outside_ram_are_ignored(self):
        text = '100008\n180009\n8\n2000000\nexisting:8\n'
        self.misses.write_text(text)
        self.assertEqual(self.run_capture(), 0)
        self.assertEqual(self.misses.read_text(), text)
        self.assertFalse(self.out.exists())

    def test_empty_page_is_not_treated_as_loaded_code(self):
        self.misses.write_text('190008\n')
        self.assertEqual(self.run_capture(), 0)
        self.assertFalse(self.out.exists())

    def test_short_ram_dump_is_rejected(self):
        with self.assertRaisesRegex(ValueError, '32 MiB'):
            capture(self.elf, b'\0' * 16, self.out, self.misses)

    def test_existing_snapshot_content_must_match(self):
        self.misses.write_text('180008\n')
        self.run_capture()
        next(self.out.glob('*.bin')).write_bytes(b'corrupted')
        self.misses.write_text('180008\n')
        with self.assertRaisesRegex(ValueError, 'collision'):
            self.run_capture()

    def test_module_miss_recaptures_code_written_after_the_first_snapshot(self):
        self.misses.write_text('180008\n')
        self.run_capture()
        old_token = self.misses.read_text()
        self.ram[0x180008:0x18000c] = b'\x08\x00\xe0\x03'
        self.assertEqual(self.run_capture(), 1)
        self.assertNotEqual(self.misses.read_text(), old_token)
        self.assertEqual(len(list(self.out.glob('*.bin'))), 2)

    def test_goal_type_requires_name_and_reciprocal_symbol_link(self):
        tag, symbol, string = 0x200004, 0x140014, 0x210004
        struct.pack_into('<I', self.ram, string, 8)
        self.ram[string + 4:string + 13] = b'function\0'
        struct.pack_into('<I', self.ram, symbol + 8167 * 8, string)
        struct.pack_into('<I', self.ram, symbol, tag)
        struct.pack_into('<I', self.ram, tag, symbol)
        struct.pack_into('<I', self.ram, 0x180000, tag)
        struct.pack_into('<I', self.ram, 0x180018, tag)
        self.assertEqual(goal_function_entries(self.ram), [0x180004, 0x18001c])
        struct.pack_into('<I', self.ram, tag, 0)
        self.assertEqual(goal_function_entries(self.ram), [])

    def test_v3_top_level_template_bounds_and_alignment(self):
        code = struct.pack('<5I', 0, 0x24030000, 0xc, 0x1000ffff, 0)
        body = bytearray(128)
        struct.pack_into('<4I', body, 0, 0, 128, 3, 3)
        struct.pack_into('<4I', body, 112, 0, 0, len(code), 0)
        body.extend(code)
        archive = struct.pack('<I60xI60x', 1, len(body)) + body
        self.assertEqual(list(templates(archive, 0x180000)), [(0x17ffe0, code)])
        with self.assertRaisesRegex(ValueError, 'truncated object body'):
            list(templates(archive[:-1], 0x180000))


if __name__ == '__main__':
    unittest.main()
