from construct import *
from construct.lib import *

class LittleEndianBitsInteger(Construct):
    r"""
    Field that packs arbitrarily large (or small) integers. Some fields (Bit Nibble Octet) use this class. Must be enclosed in :class:`~construct.core.Bitwise` context.
    Parses into an integer. Builds from an integer into specified bit count and endianness. Size (in bits) is specified in ctor.
    Note that little-endianness is only defined for multiples of 8 bits.
    Analog to :class:`~construct.core.BytesInteger` that operates on bytes. In fact, ``BytesInteger(n)`` is equivalent to ``Bitwise(BitsInteger(8*n))`` and ``BitsInteger(n)`` is equivalent to ``Bytewise(BytesInteger(n//8)))`` .
    :param length: integer or context lambda, number of bits in the field
    :param signed: bool, whether the value is signed (two's complement), default is False (unsigned)
    :param swapped: bool, whether to swap byte order (little endian), default is False (big endian)
    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises IntegerError: lenght is negative, given a negative value when field is not signed, or not an integer
    Can propagate any exception from the lambda, possibly non-ConstructError.
    Example::
        >>> d = Bitwise(BitsInteger(8)) or Bitwise(Octet)
        >>> d.parse(b"\x10")
        16
        >>> d.build(255)
        b'\xff'
        >>> d.sizeof()
        1
    """

    def __init__(self, length, signed=False, swapped=False):
        super(LittleEndianBitsInteger, self).__init__()
        self.length = length
        self.signed = signed
        self.swapped = swapped

    def _parse(self, stream, context, path):
        length = self.length
        if callable(length):
            length = length(context)
        if length < 0:
            raise IntegerError("length must be non-negative")
        data = stream_read(stream, length)
        data = swapbytes(data)
        return bits2integer(data, self.signed)

    def _build(self, obj, stream, context, path):
        if not isinstance(obj, integertypes):
            raise IntegerError("value %r is not an integer" % (obj,))
        if obj < 0 and not self.signed:
            raise IntegerError("value %r is negative, but field is not signed" % (obj,))
        length = self.length
        if callable(length):
            length = length(context)
        if length < 0:
            raise IntegerError("length must be non-negative")
        data = integer2bits(obj, length)
        data = swapbytes(data)
        stream_write(stream, data, length)
        return obj

    def _sizeof(self, context, path):
        try:
            length = self.length
            if callable(length):
                length = length(context)
            return length
        except (KeyError, AttributeError):
            raise SizeofError("cannot calculate size, key not found in context")

    def _emitparse(self, code):
        return "bits2integer(read_bytes(io, %s)%s, %s)" % (self.length, "[::-1]" if self.swapped else "", self.signed, )

    def _emitprimitivetype(self, ksy, bitwise):
        assert not self.signed
        assert not self.swapped
        return "b%s" % (self.length, )


svc_bad = Struct()
svc_nop = Struct()
svc_disconnect = Struct(
    "msg" / CString("utf8")
)
svc_event = Struct()
svc_version = Struct()
svc_setview = Struct(
    "viewentity" / Int16ul
)
svc_sound = Struct()
svc_time = Struct()

svc_print = CString("utf8")

svc_stufftext = CString("utf8")

svc_setangle = Struct()

svc_serverinfo = Struct(
    "protocol" / Int32ul,
    "server_count" / Int32ul,
    "server_crc" / Int32ul,
    "clientdllmd5" / Bytes(16),
    "maxclients" / Int8ul,
    "playernum" / Int8ul,
    "gametype" / Int8ul,
    "gamedir" / CString("utf8"),
    "hostname" / CString("utf8"),
    "levelname" / CString("utf8"),
    "skip" / CString("utf8"),
    "has_more" / Int8ul,
    "extra" / If(this.has_more != 0, Struct(
            "length" / Int8ul,
            "data" / Bytes(this.length),
            "unk" / Bytes(16),
        )
    )
)

svc_lightstyle = Struct()

svc_updateuserinfo = Struct(
    "playernumber" / Byte,
    "userid" / Int32ul,
    "infostring" / CString("utf8"),
    "hashedcdkey" / Bytes(16)
)

delta = Struct(
    "nbytes" / LittleEndianBitsInteger(3),
    "bits" / LittleEndianBitsInteger(this.nbytes * 8),
    "fieldType" / If(this.bits & 0b1 != 0, LittleEndianBitsInteger(32)),
    "fieldName" / If(this.bits & (1 << 1) != 0, Bytewise(BitsSwapped(NullTerminated(GreedyBytes, term=bytes(1))))),
    "fieldOffset" / If(this.bits & (1 << 2) != 0, LittleEndianBitsInteger(16)),
    "fieldSize" / If(this.bits & (1 << 3) != 0, LittleEndianBitsInteger(8)),
    "significant_bits" / If(this.bits & (1 << 4) != 0, LittleEndianBitsInteger(8)),
    "premultiply" / If(this.bits & (1 << 5) != 0, LittleEndianBitsInteger(32)),
    "postmultiply" / If(this.bits & (1 << 6) != 0, LittleEndianBitsInteger(32)),
    #"padding" / LittleEndianBitsInteger(5),
)

svc_deltadescription = Struct(
    "name" / CString("utf8"),
    "fieldcount" / Int16ul,
    "deltas" / BitsSwapped(Bitwise(
        Aligned(8, Array(this.fieldcount, delta))
    ))
)

svc_clientdata = Struct()
svc_stopsound = Struct()
svc_pings = Struct()
svc_particle = Struct()
svc_damage = Struct()
svc_spawnstatic = Struct()
svc_event_reliable = Struct()
svc_spawnbaseline = Struct()

TE_LENGTH = [
	24, 20,  6, 11,  6, 10, 12, 17, 16,  6,  6,  6,  8, -1,  9, 19,
	-2, 10, 16, 24, 24, 24, 10, 11, 16, 19, -2, 12, 16, -1, 19, 17,
	-2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2,
	-2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2,
	-2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2,
	-2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2,
	-2, -2, -2,  2, 10, 14, 12, 14,  9,  5, 17, 13, 24,  9, 17,  7,
	10, 19, 19, 12,  7,  7,  9, 16, 18,  6, 10, 13,  7,  1, 18, 15,
]
te_bspdecal = Struct(
    "unk1" / Bytes(8),
    "has_more" / Int16ul,
    "unk2" / If(this.has_more != 0, Bytes(2))
)
te_textmessage = Struct(
    "unk1" / Bytes(5),
    "has_more" / Int8ul,
    "unk2" / If(this.has_more == 2, Bytes(2)),
    "unk3" / Bytes(14),
    "unk4" / CString("utf8")
)
svc_temp_entity = Struct(
    "type" / Int8ul,
    "data" / Switch(this.type, {
        0: Bytes(24),
        1: Bytes(20),
        2: Bytes(6),
        3: Bytes(11),
        4: Bytes(6),
        5: Bytes(10),
        6: Bytes(12),
        7: Bytes(17),
        8: Bytes(16),
        9: Bytes(6),
        10: Bytes(6),
        11: Bytes(6),
        12: Bytes(8),
        13: te_bspdecal,
        14: Bytes(9),
        15: Bytes(19),
        17: Bytes(10),
        18: Bytes(16),
        19: Bytes(24),
        20: Bytes(24),
        21: Bytes(24),
        22: Bytes(10),
        23: Bytes(11),
        24: Bytes(16),
        25: Bytes(19),
        27: Bytes(12),
        28: Bytes(16),
        29: te_textmessage,
        30: Bytes(19),
        31: Bytes(17),
        99: Bytes(2),
        100: Bytes(10),
        101: Bytes(14),
        102: Bytes(12),
        103: Bytes(14),
        104: Bytes(9),
        105: Bytes(5),
        106: Bytes(17),
        107: Bytes(13),
        108: Bytes(24),
        109: Bytes(9),
        110: Bytes(17),
        111: Bytes(7),
        112: Bytes(10),
        113: Bytes(19),
        114: Bytes(19),
        115: Bytes(12),
        116: Bytes(7),
        117: Bytes(7),
        118: Bytes(9),
        119: Bytes(16),
        120: Bytes(18),
        121: Bytes(6),
        122: Bytes(10),
        123: Bytes(13),
        124: Bytes(7),
        125: Bytes(1),
        126: Bytes(18),
        127: Bytes(15),
    })
)

svc_setpause = Struct()

svc_signonnum = Struct(
    "num" / Byte
)

svc_centerprint = Struct()
svc_killedmonster = Struct()
svc_foundsecret = Struct()

svc_spawnstaticsound = Struct(
    "data" / Bytes(14)
)

svc_intermission = Struct()
svc_finale = Struct()

svc_cdtrack = Struct(
    "cdtrack" / Byte,
    "looptrack" / Byte
)

svc_restore = Struct()
svc_cutscene = Struct()
svc_weaponanim = Struct()
svc_decalname = Struct()
svc_roomtype = Struct()
svc_addangle = Struct()

svc_newusermsg = Struct(
    "imsg" / Byte,
    "isize" / Int8sl,
    "name" / Bytes(16)
)

svc_packetentities = Struct()
svc_deltapacketentities = Struct()
svc_choke = Struct()

resource = Struct(
    "type" / LittleEndianBitsInteger(4),
    "filename" / Bytewise(BitsSwapped(NullTerminated(GreedyBytes, term=bytes(1)))),
    "index" / LittleEndianBitsInteger(12),
    "downloadSize" / LittleEndianBitsInteger(24),
    "ucFlags" / LittleEndianBitsInteger(3),
    "rgucMD5_hash" / If(this.ucFlags & (1 << 2) != 0, Bytewise(BitsSwapped(Bytes(16)))),
    "has_reserved" / BitsInteger(1),
    "rguc_reserved" / If(this.has_reserved != 0, Bytewise(BitsSwapped(Bytes(32)))),
)

resource_extra_inner = Struct(
    "flag" / BitsInteger(1),
    "data" / IfThenElse(this.flag != 0, LittleEndianBitsInteger(5), LittleEndianBitsInteger(10)),
)
resource_extra = Struct(
    "flag" / BitsInteger(1),
    "inner" / If(this.flag != 0, resource_extra_inner)
)
svc_resourcelist = BitsSwapped(Bitwise(Aligned(8, Struct(
    "total" / LittleEndianBitsInteger(12),
    "resources" / Array(this.total, resource),
    "has_more" / BitsInteger(1),
    "extra" / If(this.has_more != 0, RepeatUntil(lambda obj,lst,ctx: obj.flag == 0, resource_extra)),
))))

svc_newmovevars = Struct(
    "gravity" / Float32l,
    "stopspeed" / Float32l,
    "maxspeed" / Float32l,
    "spectatormaxspeed" / Float32l,
    "accelerate" / Float32l,
    "airaccelerate" / Float32l,
    "wateraccelerate" / Float32l,
    "friction" / Float32l,
    "edgefriction" / Float32l,
    "waterfriction" / Float32l,
    "entgravity" / Float32l,
    "bounce" / Float32l,
    "stepsize" / Float32l,
    "maxvelocity" / Float32l,
    "zmax" / Float32l,
    "waveHeight" / Float32l,
    "footsteps" / Byte,
    "rollangle" / Float32l,
    "rollspeed" / Float32l,
    "skycolor_r" / Float32l,
    "skycolor_g" / Float32l,
    "skycolor_b" / Float32l,
    "skyvec_x" / Float32l,
    "skyvec_y" / Float32l,
    "skyvec_z" / Float32l,
    "skyName"/ CString("utf8")
)

svc_resourcerequest = Struct(
    "arg" / Int32ul,
    "startindex" / Int32ul
)

svc_customization = Struct()
svc_crosshairangle = Struct()
svc_soundfade = Struct()
svc_filetxferfailed = Struct()
svc_hltv = Struct()
svc_director = Struct()
svc_voiceinit = Struct()
svc_voicedata = Struct()

svc_sendextrainfo = Struct(
    "clientfallback" / CString("utf8"),
    "allowCheats" / Byte
)

svc_timescale = Struct()
svc_resourcelocation = Struct()
svc_sendcvarvalue = Struct()
svc_sendcvarvalue2 = Struct()

svpacket = Struct(
    "opcode" / Enum(Byte,
        svc_bad = 0x00,
        svc_nop = 0x01,
        svc_disconnect = 0x02,
        svc_event = 0x03,
        svc_version = 0x04,
        svc_setview = 0x05,
        svc_sound = 0x06,
        svc_time = 0x07,
        svc_print = 0x08,
        svc_stufftext = 0x09,
        svc_setangle = 0x0A,
        svc_serverinfo = 0x0B,
        svc_lightstyle = 0x0C,
        svc_updateuserinfo = 0x0D,
        svc_deltadescription = 0x0E,
        svc_clientdata = 0x0F,
        svc_stopsound = 0x10,
        svc_pings = 0x11,
        svc_particle = 0x12,
        svc_damage = 0x13,
        svc_spawnstatic = 0x14,
        svc_event_reliable = 0x15,
        svc_spawnbaseline = 0x16,
        svc_temp_entity = 0x17,
        svc_setpause = 0x18,
        svc_signonnum = 0x19,
        svc_centerprint = 0x1A,
        svc_killedmonster = 0x1B,
        svc_foundsecret = 0x1C,
        svc_spawnstaticsound = 0x1D,
        svc_intermission = 0x1E,
        svc_finale = 0x1F,
        svc_cdtrack = 0x20,
        svc_restore = 0x21,
        svc_cutscene = 0x22,
        svc_weaponanim = 0x23,
        svc_decalname = 0x24,
        svc_roomtype = 0x25,
        svc_addangle = 0x26,
        svc_newusermsg = 0x27,
        svc_packetentities = 0x28,
        svc_deltapacketentities = 0x29,
        svc_choke = 0x2A,
        svc_resourcelist = 0x2B,
        svc_newmovevars = 0x2C,
        svc_resourcerequest = 0x2D,
        svc_customization = 0x2E,
        svc_crosshairangle = 0x2F,
        svc_soundfade = 0x30,
        svc_filetxferfailed = 0x31,
        svc_hltv = 0x32,
        svc_director = 0x33,
        svc_voiceinit = 0x34,
        svc_voicedata = 0x35,
        svc_sendextrainfo = 0x36,
        svc_timescale = 0x37,
        svc_resourcelocation = 0x38,
        svc_sendcvarvalue = 0x39,
        svc_sendcvarvalue2 = 0x3A),
    "data" / Switch(this.opcode,
        {
            "svc_bad": svc_bad,
            "svc_nop": svc_nop,
            "svc_disconnect": svc_disconnect,
            "svc_event": svc_event,
            "svc_version": svc_version,
            "svc_setview": svc_setview,
            "svc_sound": svc_sound,
            "svc_time": svc_time,
            "svc_print": svc_print,
            "svc_stufftext": svc_stufftext,
            "svc_setangle": svc_setangle,
            "svc_serverinfo": svc_serverinfo,
            "svc_lightstyle": svc_lightstyle,
            "svc_updateuserinfo": svc_updateuserinfo,
            "svc_deltadescription": svc_deltadescription,
            "svc_clientdata": svc_clientdata,
            "svc_stopsound": svc_stopsound,
            "svc_pings": svc_pings,
            "svc_particle": svc_particle,
            "svc_damage": svc_damage,
            "svc_spawnstatic": svc_spawnstatic,
            "svc_event_reliable": svc_event_reliable,
            "svc_spawnbaseline": svc_spawnbaseline,
            "svc_temp_entity": svc_temp_entity,
            "svc_setpause": svc_setpause,
            "svc_signonnum": svc_signonnum,
            "svc_centerprint": svc_centerprint,
            "svc_killedmonster": svc_killedmonster,
            "svc_foundsecret": svc_foundsecret,
            "svc_spawnstaticsound": svc_spawnstaticsound,
            "svc_intermission": svc_intermission,
            "svc_finale": svc_finale,
            "svc_cdtrack": svc_cdtrack,
            "svc_restore": svc_restore,
            "svc_cutscene": svc_cutscene,
            "svc_weaponanim": svc_weaponanim,
            "svc_decalname": svc_decalname,
            "svc_roomtype": svc_roomtype,
            "svc_addangle": svc_addangle,
            "svc_newusermsg": svc_newusermsg,
            "svc_packetentities": svc_packetentities,
            "svc_deltapacketentities": svc_deltapacketentities,
            "svc_choke": svc_choke,
            "svc_resourcelist": svc_resourcelist,
            "svc_newmovevars": svc_newmovevars,
            "svc_resourcerequest": svc_resourcerequest,
            "svc_customization": svc_customization,
            "svc_crosshairangle": svc_crosshairangle,
            "svc_soundfade": svc_soundfade,
            "svc_filetxferfailed": svc_filetxferfailed,
            "svc_hltv": svc_hltv,
            "svc_director": svc_director,
            "svc_voiceinit": svc_voiceinit,
            "svc_voicedata": svc_voicedata,
            "svc_sendextrainfo": svc_sendextrainfo,
            "svc_timescale": svc_timescale,
            "svc_resourcelocation": svc_resourcelocation,
            "svc_sendcvarvalue": svc_sendcvarvalue,
            "svc_sendcvarvalue2": svc_sendcvarvalue2,
        }
    )
)
