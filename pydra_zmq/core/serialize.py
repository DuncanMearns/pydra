import sys
import struct
import json
import pickle
import numpy as np


def _serialize_int(i: int):
    return int(i).to_bytes(4, sys.byteorder, signed=True)


def _deserialize_int(i_bytes: bytes):
    return int.from_bytes(i_bytes, sys.byteorder, signed=True)


def _serialize_string(s: str):
    return s.encode("utf-8")


def _deserialize_string(s_bytes: bytes):
    return s_bytes.decode("utf-8")


def _serialize_float(f: float):
    return bytearray(struct.pack("d", f))


def _deserialize_float(f_bytes: bytes):
    return struct.unpack("d", f_bytes)[0]


def _to_json(d: dict):
    return json.dumps(d).encode("utf-8")


def _from_json(d_bytes: bytes):
    return json.loads(d_bytes.decode("utf-8"))


def _serialize_array(a: np.ndarray):
    return a.dumps()


def _deserialize_array(a_bytes: bytes):
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


class DataSerializer(Serializer):

    options = {

        "t": {
            "encoder": (_serialize_float, _to_json),
            "decoder": (_deserialize_float, _from_json)
        },

        "i": {
            "encoder": (_serialize_float, _serialize_int, _to_json),
            "decoder": (_deserialize_float, _deserialize_int, _from_json)
        },

        "f": {
            "encoder": (_serialize_float, _serialize_int, _serialize_array),
            "decoder": (_deserialize_float, _deserialize_int, _deserialize_array)
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
        return _serialize_string(event_name), _to_json(event_kw)

    def decode(self, event_name, event_kw):
        return _deserialize_string(event_name), _from_json(event_kw)
