from .serialize import _serialize_string, _serialize_float
from .serialize import *
import time


class MessageType:
    flag = b""
    serializer = Serializer


class MESSAGE(MessageType):
    flag = b"message"
    serializer = StringSerializer


class STATE(MessageType):
    flag = b"string"
    serializer = StateSerializer


class EXIT(STATE):
    flag = b"exit"


class DATA(MessageType):
    flag = b"data"
    serializer = DataSerializer


class OutputMessage:

    def __init__(self, message_type, *message_flags):
        self.message = message_type
        self.flags = message_flags
        self.serializer = self.message.serializer(*self.flags)

    def __call__(self, method):
        def zmq_output_wrapper(obj, *args, **kwargs):
            result = method(obj, *args, **kwargs)
            serialized = self.serializer.encode(result)
            message_flag = self.message.flag
            source = _serialize_string(obj.name)
            flags = b""
            for f in self.flags:
                flags = flags + _serialize_string(f)
            t = time.time()
            t = _serialize_float(t)
            msg = [message_flag, source, t, flags] + list(serialized)
            obj.zmq_publisher.send_multipart(msg)
            return result
        return zmq_output_wrapper
