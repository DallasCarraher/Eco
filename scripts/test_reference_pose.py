import struct
import unittest

from reference_pose import PineReads, pose


class FakeSocket:
    def __init__(self, reply):
        self.reply = reply
        self.sent = b''

    def sendall(self, data):
        self.sent += data

    def recv(self, count):
        result, self.reply = self.reply[:min(count, 2)], self.reply[min(count, 2):]
        return result


class PineTests(unittest.TestCase):
    def test_fragmented_reply(self):
        socket = FakeSocket(struct.pack('<IBII', 13, 0, 0x422f4600, 0))
        self.assertEqual(PineReads(socket).words([0x10000, 0x10004]), [0x422f4600, 0])
        self.assertEqual(socket.sent, struct.pack('<I', 14)+b'\x02'+struct.pack('<I', 0x10000)+b'\x02'+struct.pack('<I', 0x10004))

    def test_failure_and_truncation(self):
        with self.assertRaises(ValueError):
            PineReads(FakeSocket(struct.pack('<IB', 5, 255))).words([0])
        with self.assertRaises(EOFError):
            PineReads(FakeSocket(b'\x09\0')).words([0])

    def test_read_bounds(self):
        for address in (3, 32*1024*1024):
            with self.assertRaises(ValueError):
                PineReads(FakeSocket(b'')).words([address])


class Memory:
    def __init__(self):
        self.words = {}
        self.names = {0x12000: 'art-joint-anim', 0x13000: 'push'}
        for i, name in enumerate(('logo', 'camera-anim', 'volumes', 'target', 'sidekick')):
            obj, skel, group = 0x20004+i*0x1000, 0x30004+i*0x1000, 0x40004+i*0x1000
            if i:
                offset = (184, 192, 208, 216)[i-1]
                self.words[0x20004+offset-4] = 0x50000+i*4
                self.words[0x50000+i*4] = obj
            self.words.update({obj+24: obj, obj+120: skel, skel+20: 1,
                               skel+12: skel+44, skel+56: group,
                               skel+60: 0x422f4600, skel+52: 0,
                               skel+48: 0x13000, group-4: 0x11000,
                               0x11000: 0x12000, group+4: 0x60000})

    def u32(self, address):
        return self.words.get(address, 0)

    def field(self, obj, offset):
        return self.u32(obj+offset-4)

    def symbol_name(self, sym):
        return self.names.get(sym)

    def string(self, ptr):
        return 'synthetic-animation' if ptr == 0x60000 else None


class PoseTests(unittest.TestCase):
    def test_coordinated_channels(self):
        result = pose(Memory(), 0x20004)
        self.assertEqual(len(result), 5)
        self.assertTrue(all(r['frame_bits'] == 0x422f4600 for r in result.values()))

    def test_bad_camera_link(self):
        memory = Memory()
        memory.words[0x21004+24] = 0
        with self.assertRaisesRegex(ValueError, 'self link'):
            pose(memory, 0x20004)

    def test_phase_difference_preserved_exactly(self):
        memory = Memory()
        memory.words[0x31004+60] += 1
        result = pose(memory, 0x20004)
        self.assertNotEqual(result['logo']['frame_bits'], result['camera-anim']['frame_bits'])
