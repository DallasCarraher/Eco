"""Retail Jak 1 pose-input markers and bounded read-only PCSX2 PINE reads.

Exact phase equality is evidence about animation inputs, not rendered geometry.
"""
import struct


def pose(memory, logo):
    rows = {}
    objects = {'logo': logo}
    for name, offset in [('camera-anim', 184), ('volumes', 192),
                         ('target', 208), ('sidekick', 216)]:
        objects[name] = memory.u32(memory.field(logo, offset))
    for name, obj in objects.items():
        if not 0x10000 <= obj < 32*1024*1024 or memory.field(obj, 28) != obj:
            raise ValueError('invalid '+name+' self link')
        skel = memory.field(obj, 124)
        if memory.field(skel, 24) != 1 or memory.field(skel, 16) != skel+44:
            raise ValueError('unsupported '+name+' channel layout')
        channel = skel+44
        group = memory.u32(channel+12)
        if memory.symbol_name(memory.u32(memory.u32(group-4))) != 'art-joint-anim':
            raise ValueError('invalid animation group type')
        rows[name] = {'frame_bits': memory.u32(channel+16),
                      'interp_bits': memory.u32(channel+8),
                      'command': memory.symbol_name(memory.u32(channel+4)),
                      'group_name': memory.string(memory.field(group, 8)),
                      'speed_bits': memory.field(group, 20),
                      'artist_base_bits': memory.field(group, 24),
                      'artist_step_bits': memory.field(group, 28)}
        if not rows[name]['group_name']:
            raise ValueError('missing animation group name')
    return rows


class PineReads:
    def __init__(self, connection):
        self.connection = connection

    def receive(self, count):
        result = bytearray()
        while len(result) < count:
            part = self.connection.recv(count-len(result))
            if not part:
                raise EOFError('PINE reply truncated')
            result.extend(part)
        return bytes(result)

    def request(self, payload, expected):
        if len(payload) > 65536 or expected > 65536:
            raise ValueError('PINE request exceeds diagnostic bound')
        self.connection.sendall(struct.pack('<I', len(payload)+4)+payload)
        size = struct.unpack('<I', self.receive(4))[0]
        if not 5 <= size <= 65541:
            raise ValueError('invalid PINE reply length')
        reply = self.receive(size-4)
        if reply[0] != 0 or len(reply)-1 != expected:
            raise ValueError('failed or unexpected PINE reply')
        return reply[1:]

    def words(self, addresses):
        if len(addresses) > 4096 or any(a % 4 or not 0 <= a < 32*1024*1024 for a in addresses):
            raise ValueError('unaligned/out-of-RAM read')
        data = self.request(b''.join(b'\x02'+struct.pack('<I', a) for a in addresses), 4*len(addresses))
        return list(struct.unpack('<'+'I'*len(addresses), data))
