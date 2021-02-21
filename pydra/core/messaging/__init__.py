from .serializers import *
import time

__all__ = ["PydraMessage", "EXIT", "MESSAGE", "EVENT", "DATA", "TIMESTAMPED", "INDEXED", "FRAME", "LOGGED",
           "EVENT_INFO", "DATA_INFO", "TRIGGER"]


class PydraMessage:
    """Base Message class for serializing and deserializing messages passed between pydra objects.

    Parameters
    ----------
    dtypes : iterable of types
        The data types to be encoded and decoded.

    Attributes
    ----------
    dtypes : str
        Characters representing each data type to be encoded/decoded in the message.
    encoders : list of functions
        Functions for serializing each data type in the message.
    decoders : list of functions
        Functions for deserializing each data type in the message.

    Class Attributes
    ----------------
    flag : bytes
        Unique string specifying the message type represented in bytes.
    """

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
            A pydra worker object that is able to send messages over zmq.

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

    def __call__(self, method):
        """Decorator for sending messages using 0MQ.

        The wrapper function, zmq_message, runs the method and sends the result to a zmq socket along with message tags
        to assist with decoding once received.
        """
        def zmq_message(obj, *args, **kwargs):
            result = method(obj, *args, **kwargs)
            obj.zmq_publisher.send_serialized((obj, method, result), self.serializer)
            return result
        return zmq_message


class ExitMessage(PydraMessage):
    """Decorator for outputting an exit signal. Should only be used by main pydra class, or other top-level exit signal
    provider."""

    flag = b"exit"

    def __init__(self):
        super().__init__()


EXIT = ExitMessage()


class TextMessage(PydraMessage):
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


MESSAGE = TextMessage()


class EventMessage(PydraMessage):
    """Decorator for sending events."""

    flag = b"event"

    def __init__(self):
        super().__init__(str, dict)


EVENT = EventMessage()


class DataMessage(PydraMessage):
    """Decorator for sending data. Takes a data_flag as an argument for specifying the format of the data being sent,
    and an optional saved parameter."""

    flag = b"data"

    dtypes = {
        b"t": (float, dict),
        b"i": (float, int, dict),
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
FRAME = DataMessage(b"f")


class LoggedMessage(PydraMessage):
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


LOGGED = LoggedMessage()


EVENT_INFO = PydraMessage(float, str, str, dict, np.ndarray)
DATA_INFO = PydraMessage(str, dict, np.ndarray)


class TriggerMessage(PydraMessage):

    flag = b"trigger"

    def __init__(self):
        super().__init__()


TRIGGER = TriggerMessage()
