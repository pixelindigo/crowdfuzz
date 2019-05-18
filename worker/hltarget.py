from construct import *
from svpackets import svpacket
from collections import deque
from io import BytesIO
from ptracetarget import PtraceTarget
from utils import unmunge2, munge2, unmunge3
import bz2
import struct
import os
import time
import logging


class HLTarget(PtraceTarget):

    def __init__(self, *args, **kwargs):
        super().__init__(["./hlds_linux", "-game", "cstrike", "-nobreakpad", "-nomaster", "+sv_lan", "1",
                            "-steam_dir", "/home/steam/steamcmd/", "-steamcmd_script", "/home/steam/cs16-dedicated/cs16_update.txt",
                            "-ip", "0.0.0.0", "-port", "27015", "+map", "de_dust", "-insecure"],
                            {'LD_LIBRARY_PATH':".:"+os.environ.get("LD_LIBRARY_PATH", "")}, *args, **kwargs)
        self.seq = 0
        self.ack = 0
        self.usermsg = {}
        self.fragbuffers = None
        self.received_fragments = False
        self.reliable_ack = 0
        self.queue = deque()
        self.parse_packets = True

        with open('steam.cert', 'rb') as f:
            steam_cert = f.read()
            self.session = HLSession(steam_cert, self)

    def start(self):
        logging.warning('starting')
        super().start(('127.0.0.1', 27015))
        logging.warning('waiting for the start')
        time.sleep(5)
        logging.warning('sending auth')
        self.session.pre_send(self)

    def send(self, data):
        logging.warning(f'sending {data}')
        if data.startswith(b'\xff\xff\xff\xff'):
            return super().send(data)
        self.seq += 1
        msg = struct.pack('<I', self.seq) \
                + struct.pack('<I', self.ack | (self.reliable_ack << 31)) \
                + munge2(data, self.seq & 0xFF)
        return super().send(msg)

    def recv(self, max_bytes=8192):
        msg = super().recv(max_bytes)
        if msg.startswith(b'\xff\xff\xff\xff'):
            return msg[4:]
        seq, ack = struct.unpack('<II', msg[:8])

        is_reliable = (seq >> 31) != 0
        contains_fragments = (seq & (1 << 30)) != 0

        self.ack = max(self.ack, seq & 0x3FFFFFFF)

        if is_reliable:
            self.reliable_ack ^= 1

        data = unmunge2(msg[8:], seq & 0xFF)
        #logging.warning(f'recvd {data}')
        if contains_fragments:
            data = self.read_fragments(data)
        if self.parse_packets:
            length = len(data)
            bio = BytesIO(data)
            while bio.tell() != length:
                if bio.getvalue()[bio.tell()] > 0x3A:
                    #logging.warning(f'value: {bio.getvalue()[bio.tell()]}')
                    isize = self.usermsg[bio.read(1)]
                    #print(f'size: {isize}')
                    if isize == -1:
                        isize = bio.read(1)
                    bio.read(isize)
                    continue
                packet = svpacket.parse_stream(bio)
                #print(packet)
                if packet.opcode == 'svc_newusermsg':
                    self.usermsg[packet.data.imsg] = packet.data.isize
                if packet.opcode == 'svc_spawnbaseline':
                    self.parse_packets = False
                    break
                self.queue.append(packet)
        return data

    def read_fragments(self, data):
        fragments = []
        while True:
            #logging.warning(f'data: {data}')
            next_frag, data = data[0], data[1:]
            #logging.warning(f'next: {next_frag}, data: {data}')
            if next_frag == 0:
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
        #TODO: super(HLSocketConnection, self).close()
        self.seq = 0
        self.ack = 0
        self.fragbuffers = None
        self.downloaded_data = []
        self.received_fragments = False


class HLSession:

    def __init__(self, steam_cert, target_conn):
        self.steam_cert = steam_cert
        self._target_connection = target_conn

    def pre_send(self, sock):
        logging.warning('sending getchallenge')
        sock.send(b'\xff\xff\xff\xffgetchallenge steam\n')
        logging.warning('waiting for response')
        response = sock.recv()
        logging.warning(f'response {response}')
        challenge = response.split()[1]
        logging.warning(f'challenge {challenge}')

        sock.send(b'\xff\xff\xff\xffconnect 48 ' + challenge + b' "\\prot\\3\\unique\\-1\\raw\\steam\\cdkey\\9caba13b1a636eb1d0d822aa8c82fd3b" "\\_cl_autowepswitch\\1\\bottomcolor\\6\\cl_dlmax\\512\\cl_lc\\1\\cl_lw\\1\\cl_updaterate\\60\\model\\gordon\\name\\fuzzbot\\topcolor\\30\\_vgui_menus\\1\\_ah\\1\\rate\\30000"\n' + self.steam_cert)

        # TODO: check that connection is accepted
        #sock.recv()
        logging.warning(sock.recv())

        sock.send(b'\x03new\x00\x01\x01\x01')

        while True:
            sock.send(b'\x01\x01\x01\x01\x01\x01\x01\x01')
            sock.recv()
            while sock.queue:
                packet = sock.queue.popleft()
                #logging.warning(packet)
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
                    sock.send(('\x03spawn '+str(self.server_count) + ' ' + str(munged_crc) + '\x00').encode('utf8'))
                    sock.send(b'\x03jointeam 1\x00')
                    sock.send(b'\x03joinclass 3\x00')
                    return
            time.sleep(0.1)

