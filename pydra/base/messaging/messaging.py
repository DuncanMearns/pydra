"""
Module containing PydraMessage class and all built-in pydra messages.
"""
from __future__ import annotations

from .serializers import *
from ...utilities import decorator

import warnings
import time
import functools
import typing


__all__ = ["PydraMessage", "PydraCallback",
           "EXIT", "ERROR", "CONNECTION", "STRING", "EVENT", "TRIGGER",
           "DATA", "TIMESTAMPED", "INDEXED", "ARRAY", "FRAME"]


class Interpreter:
    """Class for serializing and deserializing messages.

    Parameters
    ----------
    serializers : iterable of callables
        Iterable of functions that serialize a particular data type.
    deserializers : iterable of callables
        Iterable of functions that deserialize a particular data type.
    """

    @classmethod
    def from_dtypes(cls, *dtypes: typing.Type) -> Interpreter:
        """Returns an interpreter object from data types."""
        serializers = []
        deserializers = []
        for dtype in dtypes:
            f_serialize, f_deserialize = serializer_lookup[dtype]
            serializers.append(f_serialize)
            deserializers.append(f_deserialize)
        return cls(serializers, deserializers)

    def __init__(self, serializers: typing.Iterable[callable], deserializers: typing.Iterable[callable]):
        self.serializers = serializers
        self.deserializers = deserializers

    def serialize(self, *args: typing.Any) -> typing.Iterable[bytes]:
        """Serializes each arg with its corresponding serializer."""
        out = []
        for f, arg in zip(self.serializers, args):
            out.append(f(arg))
        return out

    def deserialize(self, *bytes_: bytes) -> typing.Iterable[typing.Any]:
        """Deserializes each arg with its corresponding deserializer."""
        out = []
        for f, x in zip(self.deserializers, bytes_):
            out.append(f(x))
        return out


class PydraMessage:
    """Class for sending and receiving messages over zmq.

    Parameters
    ----------
    tag : str
        Unique message tag designating the message type.
    dtypes : tuple
        Iterable of types that are encoded by the message.
    """

    def __init__(self, tag: str, dtypes: typing.Iterable[type]):
        self.tag = tag
        self.dtypes = tuple(dtypes)
        self.interpreter = Interpreter.from_dtypes(*self.dtypes)

    def __repr__(self):
        return f"{self.tag.upper()}({self.flags})"

    @property
    def flags(self):
        return ", ".join([dtype.__name__ for dtype in self.dtypes])

    def generate_tags(self, instance: typing.Any) -> typing.List[bytes]:
        """Generates tags that are sent with the message over a zmq socket.

        Parameters
        ----------
        instance : Any
            An object with a name attribute that is able to send messages over zmq.

        Returns
        -------
        typing.List
            List of bytes containing: the message tag, source, timestamp, and additional flags.
        """
        tag = serialize_string(self.tag)  # unique message tag
        source = serialize_string(instance.name)  # the name of the object sending the message
        flags = serialize_string(self.flags)  # additional message flags
        t = time.time()
        t = serialize_float(t)  # the time at which the message was sent
        return [tag, source, t, flags]

    @staticmethod
    def read_message(tag: bytes, source: bytes, timestamp: bytes, flags: bytes, *msg: bytes) -> tuple:
        """Deserialize message tags."""
        tag = deserialize_string(tag)
        source = deserialize_string(source)
        timestamp = deserialize_float(timestamp)
        flags = deserialize_string(flags)
        return tag, source, timestamp, flags, msg

    @property
    def serializer(self) -> typing.Callable[[typing.Any], typing.Iterable[bytes]]:
        """Returns the appropriate serializer function."""
        return self.interpreter.serialize

    @property
    def deserializer(self) -> typing.Callable[[bytes], typing.Iterable[typing.Any]]:
        """Returns the appropriate deserializer function."""
        return self.interpreter.deserialize

    @decorator()
    def CALLBACK(self, method):
        """Decorator for registering callback methods that handle PydraMessages."""
        return PydraCallback(self, method)

    @decorator()
    def SEND(self, method):
        """Decorator for methods whose outputs should be published as a PydraMessage."""
        wrapper = self.generate_wrapper(method)
        wrapper = functools.wraps(method)(wrapper)
        return wrapper

    def generate_wrapper(self, method):
        """Generates a wrapper function for sending the output of methods over zmq."""
        def send_over_zmq(instance, *args, **kwargs):
            """Calls the wrapped method and broadcasts the output over zmq."""
            result = method(instance, *args, **kwargs)
            try:
                socket = instance.zmq_publisher
            except AttributeError:
                warnings.warn(f"Message failed to publish: {instance} is not a PydraPublisher.")
                socket = None
            if socket:
                message = self.generate_tags(instance)
                parts = self.serializer(*result)
                message.extend(parts)
                socket.send(*message)
            return result
        return send_over_zmq


class PydraCallback:
    """Helper callback class for registering message handlers."""

    def __init__(self, message: PydraMessage, method: typing.Callable):
        self.message = message
        self.method = method

    def __repr__(self):
        return f"{type(self).__name__}({self.message}, {repr(self.method)})"

    def __call__(self, instance, tag, source, timestamp, flags, msg_parts):
        """Calls the registered callback method with message tags passed to kwargs."""
        kwargs = {
            "tag": tag,
            "source": source,
            "timestamp": timestamp,
            "flags": flags
        }
        args = self.message.deserializer(*msg_parts)
        return self.method(instance, *args, **kwargs)


# MESSAGES
# ========

# Private backend messages
EXIT = PydraMessage("exit", ())
ERROR = PydraMessage("error", (object, str, bool))
CONNECTION = PydraMessage("connection", ())

# User messages
STRING = PydraMessage("string", (str,))
EVENT = PydraMessage("event", (str, dict))
TRIGGER = PydraMessage("trigger", ())

# Data messages
DATA = PydraMessage("data", (object,))
TIMESTAMPED = PydraMessage("data+timestamp", (float, dict))
INDEXED = PydraMessage("data+index", (int, float, dict))
ARRAY = PydraMessage("data+array", (int, float, np.ndarray))
FRAME = PydraMessage("data+frame", (int, float, np.ndarray))
