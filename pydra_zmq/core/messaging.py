from .serialize import *
import time


class ZMQMessage:

    flag = b""

    _serializers = {
        int: ("i", serialize_int, deserialize_int),
        float: ("f", serialize_float, deserialize_float),
        str: ("s", serialize_string, deserialize_string),
        dict: ("d", serialize_dict, deserialize_dict),
        np.ndarray: ("a", serialize_array, deserialize_array)
    }

    def __init__(self, *dtypes):
        super().__init__()
        self.dtypes = ""
        self.encoders = []
        self.decoders = []
        for dtype in dtypes:
            s, serializer, deserializer = self._serializers[dtype]
            self.dtypes += s
            self.encoders.append(serializer)
            self.decoders.append(deserializer)

    def encode(self, *args):
        out = []
        for encoder, arg in zip(self.encoders, args):
            out.append(encoder(arg))
        return out

    def decode(self, *args):
        out = []
        for decoder, arg in zip(self.decoders, args):
            out.append(decoder(arg))
        return out

    def message_tags(self, obj):
        source = serialize_string(obj.name)
        dtypes = serialize_string(self.dtypes)
        t = time.time()
        t = serialize_float(t)
        return [self.flag, source, t, dtypes]

    def serializer(self, args):
        obj, method, result = args
        out = self.message_tags(obj)
        out += self.encode(*result)
        return out

    @staticmethod
    def reader(parts):
        flag, source, t, flags, *args = parts
        flag = deserialize_string(flag)
        source = deserialize_string(source)
        t = deserialize_float(t)
        flags = deserialize_string(flags)
        return flag, source, t, flags, args

    @staticmethod
    def recv(sock):
        return sock.recv_serialized(ZMQMessage.reader)

    def __call__(self, method):
        def zmq_output_wrapper(obj, *args, **kwargs):
            result = method(obj, *args, **kwargs)
            obj.zmq_publisher.send_serialized((obj, method, result), self.serializer)
            return result
        return zmq_output_wrapper


class EXIT(ZMQMessage):
    """Decorator for outputting an exit signal. Should only be used by ZMQMain class."""

    flag = b"exit"

    def __init__(self):
        super().__init__()


class MESSAGE(ZMQMessage):
    """Decorator for sending a message as a string."""

    flag = b"message"

    def __init__(self):
        super().__init__(str)


message = MESSAGE()


class EVENT(ZMQMessage):
    """Decorator for sending events."""

    flag = b"event"

    def __init__(self):
        super().__init__(str, dict)


event = EVENT()


TIMESTAMPED = b"t"
INDEXED = b"i"
FRAME = b"f"


class DATA(ZMQMessage):
    """Decorator for sending data. Takes a data_flag as an argument for specifying the format of the data being sent,
    and an optional saved parameter."""

    flag = b"data"

    dtypes = {
        TIMESTAMPED: (float, dict),
        INDEXED: (float, int, dict),
        FRAME: (float, int, np.ndarray)
    }

    def __init__(self, data_flag, saved=True):
        super().__init__(*self.dtypes[data_flag])
        self.data_flags = data_flag
        if saved:
            self.data_flags += b"s"

    def message_tags(self, obj):
        source = serialize_string(obj.name)
        t = time.time()
        t = serialize_float(t)
        return [self.flag, source, t, self.data_flags]


class LOGGED(ZMQMessage):
    """Decorator for logging methods that are called."""

    flag = b"log"

    def __init__(self):
        super().__init__(str, dict)

    def serializer(self, args):
        obj, method, result = args
        name = method.__name__
        out = self.message_tags(obj)
        out += self.encode(name, result)
        return out


logged = LOGGED()


class TRIGGER(ZMQMessage):

    flag = b"trigger"

    def __init__(self):
        super().__init__()
