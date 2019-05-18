from scapy.all import *

clc_bad = 0x0
clc_nop = 0x1
clc_move = 0x2
clc_stringcmd = 0x3
clc_delta = 0x4
clc_resourcelist = 0x5
clc_tmove = 0x6
clc_fileconsistency = 0x7
clc_voicedata = 0x8
clc_hltv = 0x9
clc_cvarvalue = 0xa
clc_cvarvalue2 = 0xb

clc_commands = { 0x0: 'clc_bad',
                 0x1: 'clc_nop',
                 0x2: 'clc_move',
                 0x3: 'clc_stringcmd',
                 0x4: 'clc_delta',
                 0x5: 'clc_resourcelist',
                 0x6: 'clc_tmove',
                 0x7: 'clc_fileconsistency',
                 0x8: 'clc_voicedata',
                 0x9: 'clc_hltv',
                 0xa: 'clc_cvarvalue',
                 0xb: 'clc_cvarvalue2'
                 }


class Base(Packet):
    name = "BasePacket"
    fields_desc=[ ByteEnumField("cmd", 0, clc_commands) ]

class Nop(Packet):
    name = "NopPacket"
    fields_desc=[]

class StringCmd(Packet):
    name = "StringCmdPacket"
    fields_desc=[ StrNullField("string", "") ]

class VoiceData(Packet):
    name = "VoiceDataPacket"
    fields_desc=[ FieldLenField("len", None, fmt="<H", length_of="data"),
                    StrLenField("data", "", length_from = lambda pkt: pkt.len) ]

class CVarValue(Packet):
    name = "CVarValuePacket"
    fields_desc=[ StrNullField("string", "") ]

class CVarValue2(Packet):
    name = "CVarValue2Packet"
    fields_desc=[ LEShortField("val", 0),
                    StrNullField("string1", ""),
                    StrNullField("string2", "") ]

bind_layers(Base, Nop, cmd=clc_nop)
bind_layers(Base, StringCmd, cmd=clc_stringcmd)
bind_layers(Base, VoiceData, cmd=clc_voicedata)
bind_layers(Base, CVarValue, cmd=clc_cvarvalue)
bind_layers(Base, CVarValue2, cmd=clc_cvarvalue2)

proto = {'base': Base(),
         #'messages': [Nop(), StringCmd(), VoiceData(), CVarValue(), CVarValue2()]}
         'messages': [VoiceData()]}
