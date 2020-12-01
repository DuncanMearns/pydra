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

    def __call__(self, method):
        def zmq_output_wrapper(obj, *args, **kwargs):
            result = method(obj, *args, **kwargs)
            serialized = self.encode(*result)
            source = serialize_string(obj.name)
            dtypes = serialize_string(self.dtypes)
            t = time.time()
            t = serialize_float(t)
            msg = [self.flag, source, t, dtypes] + serialized
            obj.zmq_publisher.send_multipart(msg)
            return result
        return zmq_output_wrapper

    @staticmethod
    def recv(sock):
        flag, source, t, dtypes, *args = sock.recv_multipart()
        flag = deserialize_string(flag)
        source = deserialize_string(source)
        t = deserialize_float(t)
        dtypes = deserialize_string(dtypes)
        return flag, source, t, dtypes, args


class EXIT(ZMQMessage):

    flag = b"exit"

    def __init__(self):
        super().__init__()


class MESSAGE(ZMQMessage):

    flag = b"message"

    def __init__(self):
        super().__init__(str)


class EVENT(ZMQMessage):

    flag = b"event"

    def __init__(self):
        super().__init__(str, dict)


TIMESTAMPED = b"t"
INDEXED = b"i"
FRAME = b"f"


class DATA(ZMQMessage):

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

    def __call__(self, method):
        def zmq_output_wrapper(obj, *args, **kwargs):
            result = method(obj, *args, **kwargs)
            serialized = self.encode(*result)
            source = serialize_string(obj.name)
            t = time.time()
            t = serialize_float(t)
            msg = [self.flag, source, t, self.data_flags] + serialized
            obj.zmq_publisher.send_multipart(msg)
            return result
        return zmq_output_wrapper


# class output:
#
#     def __init__(self, message_type, *message_flags):
#         self.message = message_type
#         self.flags = message_flags
#         self.serializer = self.message.serializer(*self.flags)
#
#     def __call__(self, method):
#         def zmq_output_wrapper(obj, *args, **kwargs):
#             result = method(obj, *args, **kwargs)
#             serialized = self.serializer.encode(result)
#             message_flag = self.message.flag
#             source = serialize_string(obj.name)
#             flags = b""
#             for f in self.flags:
#                 flags = flags + serialize_string(f)
#             t = time.time()
#             t = serialize_float(t)
#             msg = [message_flag, source, t, flags] + list(serialized)
#             obj.zmq_publisher.send_multipart(msg)
#             return result
#         return zmq_output_wrapper
#
#
# def logged(method):
#     def zmq_output_wrapper(obj, **kwargs):
#         ret = method(obj, **kwargs)
#         name = method.__name__
#         kw = {"event_name": name,
#               "ret": int(ret)}
#         serialized = EVENT.serializer().encode(("log_event", kw))
#         message_flag = EVENT.flag
#         source = serialize_string(obj.name)
#         flags = b""
#         t = time.time()
#         t = serialize_float(t)
#         msg = [message_flag, source, t, flags] + list(serialized)
#         obj.zmq_publisher.send_multipart(msg)
#         return ret
#     return zmq_output_wrapper
