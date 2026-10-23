import struct
import unittest

from reference_event_markers import Markers, SYMINFO


class MarkerTests(unittest.TestCase):
    def setUp(self):
        self.ram = bytearray(1024*1024)
        self.next_sym = 0x10004
        self.next_string = 0x40004
        self.tag = 0x30004
        self.symbol('symbol', self.tag)
        self.put(self.tag, 0x10004)
        self.symbol('logo', 0x30104)
        self.put(0x30104, 0x1000c)
        self.symbol('*active-pool*', 0x50004)
        self.symbol('*art-control*', 0x54004)
        state = self.symbol('startup', 0)
        status = self.symbol('waiting-to-run', 0)
        false = self.symbol('#f', 0)
        self.put(false, false)
        self.put(0x50004+24, 0x50004)  # self
        self.put(0x50004+16, 0x70000)  # child pointer
        self.put(0x70000, 0x51004)
        self.put(0x51000, 0x30104)  # logo type
        self.put(0x51004+20, 0x70000)  # ppointer
        self.put(0x51004+24, 0x51004)  # self
        self.put(0x51004+12, false)  # GOAL list terminator is not zero
        self.put(0x51004+32, status)
        self.put(0x51004+52, 0x52004)
        self.put(0x52004, state)
        self.put(0x51004+224, 0x53004)
        self.put(0x53004+12, self.string('synthetic-sequence'))
        self.put(0x53004+16, 3)
        self.put(0x53004+20, 4)
        self.put(0x54004+172, self.string('synthetic-sequence'))

    def put(self, at, value):
        struct.pack_into('<I', self.ram, at, value)

    def string(self, text):
        ptr = self.next_string
        self.next_string += 512
        self.put(ptr, len(text))
        self.ram[ptr+4:ptr+5+len(text)] = text.encode()+b'\0'
        return ptr

    def symbol(self, name, value):
        sym = self.next_sym
        self.next_sym += 8
        self.put(sym-4, self.tag)
        self.put(sym, value)
        self.put(sym+SYMINFO+4, self.string(name))
        return sym

    def test_active_state_and_stream(self):
        result = Markers(self.ram).report()
        self.assertEqual(result['active_art_stream'], 'synthetic-sequence')
        self.assertEqual(result['active_logo_processes'][0]['state'], 'startup')
        self.assertEqual(result['active_logo_processes'][0]['anim_parts'], 4)
        self.assertFalse(result['visual_alignment_verified'])

    def test_broken_process_backlink_rejected(self):
        self.put(0x51004+20, 0)
        with self.assertRaisesRegex(ValueError, 'backlink'):
            Markers(self.ram).report()

    def test_tree_cycle_rejected(self):
        self.put(0x51004+12, 0x70000)
        with self.assertRaisesRegex(ValueError, 'sibling'):
            Markers(self.ram).report()

    def test_unterminated_string_unavailable(self):
        ptr = self.string('example')
        self.ram[ptr+4+7] = 1
        self.assertIsNone(Markers(self.ram).string(ptr))
