from .serializers import *

import zmq
import warnings
import time


__all__ = ["PydraMessage", "EXIT", "CONNECTION", "MESSAGE", "EVENT", "DATA", "TIMESTAMPED", "INDEXED", "ARRAY", "FRAME",
           "LOGGED", "EVENT_INFO", "DATA_INFO", "TRIGGER"]


def PUB(obj) -> zmq.Socket:
    try:
        return obj.zmq_publisher.socket
    except AttributeError:
        warnings.warn(f"Message failed to publish: Pydra object {obj} is not a publisher.")


def PUSH(obj) -> zmq.Socket:
    try:
        return obj.zmq_sender.socket
    except AttributeError:
        warnings.warn(f"Message failed to send: Pydra object {obj} is not a sender.")


class PydraMessage:
    """Base Message class for serializing and deserializing messages passed between pydra objects.

    Parameters
    ----------
    dtypes : iterable of types
        The data types to be encoded and decoded.

    Attributes
    ----------
    flag : bytes
        Unique string specifying the message type represented in bytes (class attribute).
    dtypes : str
        Characters representing each data type to be encoded/decoded in the message.
    encoders : list of functions
        Functions for serializing each data type in the message.
    decoders : list of functions
        Functions for deserializing each data type in the message.
    """

    flag = b""

    _serializers = {
        bool: ("b", serialize_bool, deserialize_bool),
        int: ("i", serialize_int, deserialize_int),
        float: ("f", serialize_float, deserialize_float),
        str: ("s", serialize_string, deserialize_string),
        dict: ("d", serialize_dict, deserialize_dict),
        np.ndarray: ("a", serialize_array, deserialize_array)
    }

    def __init__(self, *dtypes, socktype=PUB):
        self.get_socket = socktype
        self.dtypes = ""
        self.encoders = []
        self.decoders = []
        for dtype in dtypes:
            s, serializer, deserializer = self._serializers[dtype]
            self.dtypes += s
            self.encoders.append(serializer)
            self.decoders.append(deserializer)

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__str__()

    def encode(self, *args):
        """Encodes parts of a message.

        Parameters
        ----------
        args : iterable
            Iterable of values with same types as specified in the constructor.

        Returns
        -------
        list
            List of bytes encoding serialized parts of the message.
        """
        out = []
        for encoder, arg in zip(self.encoders, args):
            out.append(encoder(arg))
        return out

    def decode(self, *args):
        """Decodes parts of a message.

        Parameters
        ----------
        args : iterable
            Iterable of bytes to be decoded into data types specified in the constructor.

        Returns
        -------
        list
            Deserialized list of objects.
        """
        out = []
        for decoder, arg in zip(self.decoders, args):
            out.append(decoder(arg))
        return out

    def message_tags(self, obj):
        """Generates tags that are sent with the message over a zmq socket.

        Parameters
        ----------
        obj
            A PydraObject that is able to send messages over zmq.

        Returns
        -------
        list
            List of bytes containing: the message flag, source, timestamp, and additional flags for decoding message.
        """
        source = serialize_string(obj.name)    # the name of the object/worker sending the message
        flags = serialize_string(self.dtypes)  # flags for decoding the message
        t = time.time()
        t = serialize_float(t)                 # the time at which the message was sent
        return [self.flag, source, t, flags]

    def serializer(self, args):
        """Method called by wrapper to serialize the message and tags before sending over zmq."""
        obj, method, result = args
        out = self.message_tags(obj)
        out += self.encode(*result)
        return out

    @staticmethod
    def reader(parts):
        """Decodes message tags and returns them along with serialized message.

        Returns
        -------
        tuple
            Message flag, source, timestamp, additional flags and serialized parts of message
        """
        flag, source, t, flags, *args = parts
        flag = deserialize_string(flag)
        source = deserialize_string(source)
        t = deserialize_float(t)
        flags = deserialize_string(flags)
        return flag, source, t, flags, args

    @staticmethod
    def recv(sock):
        """Receives message from a zmq socket with message tags deserialized."""
        return sock.recv_serialized(PydraMessage.reader)

    def callback(self, method):
        def decode_message(obj, *args, **kwargs):
            args = self.decode(*args)
            result = method(obj, *args, **kwargs)
            return result
        return decode_message

    def __call__(self, method):
        """Decorator for sending messages using ZeroMQ.

        The wrapper function, zmq_message, runs the method and sends the result to a zmq socket along with message tags
        to assist with decoding once received.
        """
        def zmq_message(obj, *args, **kwargs):
            result = method(obj, *args, **kwargs)
            socket = self.get_socket(obj)
            if socket:
                socket.send_serialized((obj, method, result), self.serializer)
            return result
        return zmq_message


ExitMessage = type("ExitMessage", (PydraMessage,), {"flag": b"exit"})
EXIT = ExitMessage()


class ConnectionMessage(PydraMessage):

    flag = b"connection"

    def __init__(self):
        super().__init__(bool)


CONNECTION = ConnectionMessage()


class StringMessage(PydraMessage):
    """Decorator for sending a message as a string."""

    flag = b"message"

    def __init__(self):
        super().__init__(str)

    def serializer(self, args):
        """Method called by wrapper to serialize the message and tags before sending over zmq."""
        obj, method, result = args
        out = self.message_tags(obj)
        out += self.encode(result)
        return out


MESSAGE = StringMessage()


class EventMessage(PydraMessage):
    """Decorator for sending events."""

    flag = b"event"

    def __init__(self):
        super().__init__(str, dict)


EVENT = EventMessage()


class DataMessage(PydraMessage):
    """Decorator for sending data. Takes a data_flag as an argument for specifying the format of the data being sent."""

    flag = b"data"

    dtypes = {
        b"t": (float, dict),
        b"i": (float, int, dict),
        b"a": (float, int, np.ndarray),
        b"f": (float, int, np.ndarray)
    }

    def __init__(self, data_flag):
        super().__init__(*self.dtypes[data_flag])
        self.data_flags = data_flag

    def message_tags(self, obj):
        source = serialize_string(obj.name)
        t = time.time()
        t = serialize_float(t)
        return [self.flag, source, t, self.data_flags]


DATA = DataMessage
TIMESTAMPED = DataMessage(b"t")
INDEXED = DataMessage(b"i")
ARRAY = DataMessage(b"a")
FRAME = DataMessage(b"f")


class LoggedMessage(PydraMessage):
    """Decorator for logging events."""

    flag = b"log"

    def __init__(self):
        super().__init__(str, dict)

    def serializer(self, args):
        obj, method, result = args
        name = method.__name__
        out = self.message_tags(obj)
        out += self.encode(name, result)
        return out


LOGGED = LoggedMessage()

# INFO message for sending event info between saver and pydra
EVENT_INFO = PydraMessage(float, str, str, dict, np.ndarray)
# INFO message for sending data info between saver and pydra
DATA_INFO = PydraMessage(str, dict, np.ndarray)


class TriggerMessage(PydraMessage):

    flag = b"trigger"

    def __init__(self):
        super().__init__()


TRIGGER = TriggerMessage()
