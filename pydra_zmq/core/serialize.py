import sys
import struct


def _serialize_int(i: int):
    return int(i).to_bytes(4, sys.byteorder, signed=True)


def _deserialize_int(i_bytes: bytes):
    return int.from_bytes(i_bytes, sys.byteorder, signed=True)


def _serialize_string(s: str):
    return s.encode("utf-8")


def _deserialize_string(s_bytes: bytes):
    return s_bytes.decode("utf-8")


def _serialize_float(f: float):
    return bytearray(struct.pack("f", f))


def _deserialize_float(f_bytes: bytes):
    return struct.unpack("f", f_bytes)


class Serializer:

    def __init__(self, *flags):
        super().__init__(*flags)

    def encode(self, *args):
        return (b"", )

    def decode(self, *args):
        return True


class StringSerializer(Serializer):

    def __init__(self, *flags):
        super().__init__(*flags)

    def encode(self, s):
        return (_serialize_string(s), )

    def decode(self, s):
        return _deserialize_string(s)


class StateSerializer(Serializer):

    def __init__(self, *flags):
        super().__init__(*flags)

    def encode(self, arg):
        state, val = arg
        return _serialize_string(state), _serialize_int(val)

    def decode(self, state, val):
        return _deserialize_string(state), _deserialize_int(val)
