from scapy.all import *

CMD_NOP = 0x0
CMD_ECHO = 0x1
CMD_READ = 0x2
CMD_WRITE = 0x3

class Base(Packet):
    name = "BasePacket"
    fields_desc=[ EnumByteField("cmd", 0, [CMD_NOP, CMD_ECHO, CMD_READ, CMD_WRITE]) ]

class Nop(Packet):
    name = "NopPacket"
    fields_desc=[]

class Echo(Packet):
    name = "EchoPacket"
    fields_desc=[ XIntField("value", 0) ]

class Read(Packet):
    name = "ReadPacket"
    fields_desc=[ XIntField("key", 0) ]

class Write(Packet):
    name = "WritePacket"
    fields_desc=[ XLEIntField("key", 0),
                  XLEIntField("value", 0)]

bind_layers(Base, Nop, cmd=CMD_NOP)
bind_layers(Base, Echo, cmd=CMD_ECHO)
bind_layers(Base, Read, cmd=CMD_READ)
bind_layers(Base, Write, cmd=CMD_WRITE)

proto = {'base': Base,
         'messages': [Nop, Echo, Read, Write]}
