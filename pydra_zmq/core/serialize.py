import sys
import struct
import json
import pickle
import numpy as np


def serialize_int(i: int):
    return int(i).to_bytes(4, sys.byteorder, signed=True)


def deserialize_int(i_bytes: bytes):
    return int.from_bytes(i_bytes, sys.byteorder, signed=True)


def serialize_string(s: str):
    return s.encode("utf-8")


def deserialize_string(s_bytes: bytes):
    return s_bytes.decode("utf-8")


def serialize_float(f: float):
    return bytearray(struct.pack("d", f))


def deserialize_float(f_bytes: bytes):
    return struct.unpack("d", f_bytes)[0]


def serialize_dict(d: dict):
    return json.dumps(d).encode("utf-8")


def deserialize_dict(d_bytes: bytes):
    return json.loads(d_bytes.decode("utf-8"))


def serialize_array(a: np.ndarray):
    return a.dumps()


def deserialize_array(a_bytes: bytes):
    return pickle.loads(a_bytes)


class Serializer:

    def __init__(self, *flags):
        self.flags = flags

    def encode(self, args):
        return (b"", )

    def decode(self, *args):
        return True


class StringSerializer(Serializer):

    def __init__(self, *flags):
        super().__init__(*flags)

    def encode(self, s):
        return (serialize_string(s),)

    def decode(self, s):
        return deserialize_string(s)


class StateSerializer(Serializer):

    def __init__(self, *flags):
        super().__init__(*flags)

    def encode(self, arg):
        state, val = arg
        return serialize_string(state), serialize_int(val)

    def decode(self, state, val):
        return deserialize_string(state), deserialize_int(val)


class DataSerializer(Serializer):

    options = {

        "t": {
            "encoder": (serialize_float, serialize_dict),
            "decoder": (deserialize_float, deserialize_dict)
        },

        "i": {
            "encoder": (serialize_float, serialize_int, serialize_dict),
            "decoder": (deserialize_float, deserialize_int, deserialize_dict)
        },

        "f": {
            "encoder": (serialize_float, serialize_int, serialize_array),
            "decoder": (deserialize_float, deserialize_int, deserialize_array)
        }
    }

    def __init__(self, *flags):
        super().__init__(*flags)
        self.encoders = self.options[self.flags[0][0].lower()]["encoder"]
        self.decoders = self.options[self.flags[0][0].lower()]["decoder"]

    def encode(self, args):
        out = []
        for encoder, arg in zip(self.encoders, args):
            out.append(encoder(arg))
        return out

    def decode(self, *args):
        out = []
        for decoder, arg in zip(self.decoders, args):
            out.append(decoder(arg))
        return out


class EventSerializer(Serializer):

    def __init__(self, *flags):
        super().__init__(*flags)

    def encode(self, args):
        event_name, event_kw = args
        return serialize_string(event_name), serialize_dict(event_kw)

    def decode(self, event_name, event_kw):
        return deserialize_string(event_name), deserialize_dict(event_kw)
