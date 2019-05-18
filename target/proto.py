import bz2
import struct
from boofuzz import Session, SocketConnection
from utils import unmunge2, munge2, unmunge3
import time
from construct import *
from collections import deque
from io import BytesIO
from svpackets import svpacket
import binascii


class HLSocketConnection(SocketConnection):

    def __init__(self, *args, **kwargs):
        super(HLSocketConnection, self).__init__(*args, proto='udp', **kwargs)
        self.seq = 0
        self.ack = 0
        self.usermsg = {}
        self.fragbuffers = None
        self.received_fragments = False
        self.reliable_ack = 0
        self.packets = deque()
        self.parse_packets = True

    def send(self, data):
        if data.startswith(b'\xff\xff\xff\xff'):
            return super(HLSocketConnection, self).send(data)
        self.seq += 1
        msg = struct.pack('<I', self.seq) \
                + struct.pack('<I', self.ack | (self.reliable_ack << 31)) \
                + munge2(data, self.seq & 0xFF)
        return super(HLSocketConnection, self).send(msg)

    def recv(self, max_bytes):
        msg = super(HLSocketConnection, self).recv(max_bytes)
        if msg.startswith(b'\xff\xff\xff\xff'):
            return msg[4:]
        seq, ack = struct.unpack('<II', msg[:8])

        is_reliable = (seq >> 31) != 0
	contains_fragments = (seq & (1 << 30)) != 0

        self.ack = max(self.ack, seq & 0x3FFFFFFF)

        if is_reliable:
            self.reliable_ack ^= 1

        data = unmunge2(msg[8:], seq & 0xFF)
        print('data', binascii.hexlify(data))
        if contains_fragments:
            data = self.read_fragments(data)
            print('received_fragments', binascii.hexlify(data))
        if self.parse_packets:
            length = len(data)
            bio = BytesIO(data)
            while bio.tell() != length:
                if ord(bio.getvalue()[bio.tell()]) > 0x3A:
                    print('value:', ord(bio.getvalue()[bio.tell()]))
                    isize = self.usermsg[ord(bio.read(1))]
                    print('size:', isize)
                    if isize == -1:
                        isize = ord(bio.read(1))
                    bio.read(isize)
                    continue
                packet = svpacket.parse_stream(bio)
                print(packet)
                if packet.opcode == 'svc_newusermsg':
                    self.usermsg[packet.data.imsg] = packet.data.isize
                if packet.opcode == 'svc_spawnbaseline':
                    self.parse_packets = False
                    break
                self.packets.append(packet)
        return data

    def read_fragments(self, data):
        fragments = []
        while True:
            next_frag, data = data[0], data[1:]
            if next_frag == b'\x00':
                break
            fragments.append(struct.unpack('<IHH', data[:8]))
            data = data[8:]
        main_offset = 0
        for fragid, frag_offset, frag_length in fragments:
            frag_offset -= main_offset
            fragcount = fragid & 0xFFFF
            fragid = (fragid >> 16) & 0xFFFF
            fragdata = data[frag_offset:frag_offset + frag_length]
            data = data[:frag_offset] + data[frag_offset + frag_length:]
            main_offset -= frag_length
            if not self.fragbuffers:
                self.fragbuffers = [None] * fragcount
            self.fragbuffers[fragid - 1] = fragdata
            is_full = True
            for f in self.fragbuffers:
                if not f:
                    is_full = False
            if is_full:
                tmp = b''.join(self.fragbuffers)
                if tmp.startswith(b'BZ2\x00'):
                    tmp = bz2.decompress(tmp[4:])
                data += tmp
                self.fragbuffers = None
        return data

    def close(self):
        self.send(b'\x03dropclient\n\x00')
        self.send(b'\x03dropclient\n\x00')
        self.send(b'\x03dropclient\n\x00')
        super(HLSocketConnection, self).close()
        self.seq = 0
        self.ack = 0
        self.fragbuffers = None
        self.downloaded_data = []
        self.received_fragments = False


class HLSession(Session):

    def __init__(self, steam_cert, *args, **kwargs):
        super(HLSession, self).__init__(*args, **kwargs)
        self.steam_cert = steam_cert

    def pre_send(self, sock):
        sock.send(b'\xff\xff\xff\xffgetchallenge steam\n')
        response = sock.recv()
        challenge = response.split()[1]

        sock.send(b'\xff\xff\xff\xffconnect 48 ' + challenge + b' "\\prot\\3\\unique\\-1\\raw\\steam\\cdkey\\9caba13b1a636eb1d0d822aa8c82fd3b" "\\_cl_autowepswitch\\1\\bottomcolor\\6\\cl_dlmax\\512\\cl_lc\\1\\cl_lw\\1\\cl_updaterate\\60\\model\\gordon\\name\\fuzzbot\\topcolor\\30\\_vgui_menus\\1\\_ah\\1\\rate\\30000"\n' + self.steam_cert)

        # TODO: check that connection is accepted
        #sock.recv()
        print(sock.recv())

        sock.send(b'\x03new\x00\x01\x01\x01')

        while True:
            sock.send(b'\x01\x01\x01\x01\x01\x01\x01\x01')
            sock.recv()
            while sock._target_connection.packets:
                packet = sock._target_connection.packets.popleft()
                print(packet)
                if packet.opcode == 'svc_serverinfo':
                    munged_crc = struct.pack('<I', packet.data.server_crc)
                    unmunged_crc = unmunge3(munged_crc, (-1 - packet.data.playernum) & 0xFF)
                    self.server_crc = unmunged_crc
                    self.server_count = packet.data.server_count
                    sock.send(b'\x03sendres\x00\x01\x01\x01')
                elif packet.opcode == 'svc_resourcerequest':
                    sock.send(b'\x05\x00\x00\x01')
                elif packet.opcode == 'svc_resourcelist':
                    munged_crc = munge2(self.server_crc, (-1 - self.server_count) & 0xFF)
                    munged_crc = struct.unpack('<i', munged_crc)[0]
                    sock.send('\x03spawn '+str(self.server_count) + ' ' + str(munged_crc) + '\x00')
                    sock.send(b'\x03jointeam 1\x00')
                    sock.send(b'\x03joinclass 3\x00')
            time.sleep(0.1)

        #print(sock._target_connection.downloaded_data.pop())
        #sock._target_connection.downloaded_data = []

        sock.send(b'\x03sendres\x00')

        while not sock._target_connection.downloaded_data:
            sock.send(b'\x01\x01\x01\x01\x01\x01\x01\x01')
            print(sock.recv())

        sock._target_connection.downloaded_data = []

        sock.send(b'\x05\x00\x00\x01')

        sock.send(b'\x03VModEnable 1\x00')

        sock.send(b'\x03jointeam 1\x00')
        sock.send(b'\x03joinclass 3\x00')
        while True:
            sock.send(b'\x01\x01\x01\x01\x01\x01\x01\x01')
            print(sock.recv())
            time.sleep(0.5)
        #sock.send(b'\x03specmode 3\x00')
        #sock.send(b'\x03specmode 3\x00')
        #sock.send(b'\x03unpause\x00')
        #sock.send(b'\x03unpause\x00')
        #sock.send(b'\x03unpause\x00')

