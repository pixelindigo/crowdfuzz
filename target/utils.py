import struct

MUNGIFY_TABLE = [ 0x7A, 0x64, 0x05, 0xF1, 0x1B, 0x9B, 0xA0, 0xB5, 0xCA, 0xED, 0x61, 0x0D, 0x4A, 0xDF, 0x8E, 0xC7 ]
MUNGIFY_TABLE2 = [ 0x05, 0x61, 0x7A, 0xED, 0x1B, 0xCA, 0x0D, 0x9B, 0x4A, 0xF1, 0x64, 0xC7, 0xB5, 0x8E, 0xDF, 0xA0 ]
MUNGIFY_TABLE3 = [ 0x20, 0x07, 0x13, 0x61, 0x03, 0x45, 0x17, 0x72, 0x0A, 0x2D, 0x48, 0x0C, 0x4A, 0x12, 0xA9, 0xB5 ]

def munge(data, table, seq):
    res = b''
    for i in range(len(data) // 4):
        chunk = struct.unpack('<I', data[4 * i: 4 * (i + 1)])[0]
        chunk ^= (~seq & 0xFFFFFFFF)
        # Reverse bytes
        chunk = struct.unpack('<I', struct.pack('>I', chunk))[0]
        table_chunk = \
          (table[(i + 3) & 0x0F] << 24) \
        | (table[(i + 2) & 0x0F] << 16) \
        | (table[(i + 1) & 0x0F] << 8) \
        | (table[(i + 0) & 0x0F]) \
        | 0xBFAFA7A5
        chunk ^= table_chunk
        chunk ^= seq
        res += struct.pack('<I', chunk)
    if len(data) % 4 > 0:
        res += data[-(len(data) % 4):]
    return res

def unmunge(data, table, seq):
    res = b''
    for i in range(len(data) // 4):
        chunk = struct.unpack('<I', data[4 * i: 4 * (i + 1)])[0]
        chunk ^= seq
        table_chunk = \
          (table[(i + 3) & 0x0F] << 24) \
        | (table[(i + 2) & 0x0F] << 16) \
        | (table[(i + 1) & 0x0F] << 8) \
        | (table[(i + 0) & 0x0F]) \
        | 0xBFAFA7A5
        chunk ^= table_chunk
        # Reverse bytes
        chunk = struct.unpack('<I', struct.pack('>I', chunk))[0]
        chunk ^= (~seq & 0xFFFFFFFF)
        res += struct.pack('<I', chunk)
    if len(data) % 4 > 0:
        res += data[-(len(data) % 4):]
    return res

def munge2(data, seq):
    return munge(data, MUNGIFY_TABLE2, seq)

def unmunge2(data, seq):
    return unmunge(data, MUNGIFY_TABLE2, seq)

def unmunge3(data, seq):
    return unmunge(data, MUNGIFY_TABLE3, seq)

if __name__ == '__main__':
    print(unmunge(b'\x72\x6a\x64\x44\x34\x6c\x73\x77\x4d\x64\x2e\x22\x00', MUNGIFY_TABLE2, 0x47))
    print(munge2(unmunge2(b'\x72\x6a\x64\x44\x34\x6c\x73\x77\x4d\x64\x2e\x22\x00', 0x47), 0x47))
