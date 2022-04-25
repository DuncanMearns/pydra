import sys
import struct
import json
import pickle
import numpy as np


def serialize_bool(b: bool):
    if b:
        return serialize_int(1)
    return serialize_int(0)


def deserialize_bool(b_bytes: bytes):
    i = deserialize_int(b_bytes)
    if i:
        return True
    return False


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


def serialize_objet(o: object):
    return pickle.dumps(o)


def deserialize_object(o_bytes: bytes):
    return pickle.loads(o_bytes)
