"""
Module with base PydraObjects.

Core functionality is provided via the PydraType metaclass, which ensures all PydraObjects have a name attribute and
callback methods for receiving PydraMessages. Two heritable PydraObject subclasses are provided for sending and
receiving pydra messages: PydraSender and PydraReceiver, respectively.
"""
from .messaging import *
from .messaging.handlers import *

import typing
import numpy as np
import warnings
import traceback


__all__ = ("PydraType", "PydraObject", "PydraSender", "PydraReceiver")


class PydraType(type):
    """Metaclass for Pydra objects initializes the name attribute and message callback methods."""

    def __new__(mcs, name, bases, namespace, **kwargs):
        if "name" not in namespace:
            namespace["name"] = name
        return super().__new__(mcs, name, bases, namespace, **kwargs)

    def __init__(cls, name, bases, namespace):
        super().__init__(name, bases, namespace)
        cls.msg_callbacks = {}  # create dictionary for message callback methods
        for parent in reversed(cls.__mro__):  # check parent classes for callbacks
            for key, attr in parent.__dict__.items():
                if isinstance(attr, PydraCallback):
                    cls.msg_callbacks[attr.message.tag] = attr


class PydraObject(metaclass=PydraType):
    """Base Pydra object class."""

    name = ""

    def __init__(self, *args, **kwargs):
        super().__init__()

    def exit(self):
        return

    def raise_error(self, error: Exception, message: str):
        raise error


class PydraSender(PydraObject):
    """Class that allows objects to send PydraMessages.

    Parameters
    ----------
    publisher : str
        Address to bind a ZMQPublisher object for broadcasting messages to pydra network.

    Notes
    -----
    Implements senders for basic message types (STRING, TRIGGER, EVENT).
    """

    def __init__(self, publisher: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if publisher:
            self.zmq_publisher = ZMQPublisher(publisher)
        else:
            warnings.warn(f"publisher address not specified for {self.name}")

    @STRING.SEND
    def send_string(self, s):
        """Publishes a string to the pydra network."""
        return s,

    @TRIGGER.SEND
    def send_trigger(self):
        """Simple method for implementing sending trigger messages."""
        return ()

    @EVENT.SEND
    def send_event(self, event_name, **kwargs):
        """Primary method for publishing EVENT messages to the pydra network.

        Parameters
        ----------
        event_name : str
            The name of the event. Other pydra objects subscribing to events from this one will call their corresponding
            callback method.

        Other Parameters
        ----------------
            Keyword arguments associated with the event."""
        return event_name, kwargs


class PydraReceiver(PydraObject):
    """Class that allows objects to receive PydraMessages.

    Parameters
    ----------
    subscriptions : iterable
        Iterable of (name, address, messages).

    Notes
    -----
    Implements callbacks for many message types.
    """

    def __init__(self, subscriptions: typing.Iterable[typing.Tuple[str, str, typing.Iterable]] = (), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.zmq_poller = ZMQPoller()
        # Set dictionaries for overwriting message and event handlers
        self.event_callbacks = {}
        for (name, addr, messages) in subscriptions:
            self.zmq_poller.add_subscription(name, addr, messages)

    def poll(self, timeout=0) -> typing.Iterable:
        """Gets messages from connected zmq ports."""
        return self.zmq_poller.poll(timeout)

    def _handle_message(self, tag: bytes, source: bytes, timestamp: bytes, flags: bytes, msg: typing.Iterable):
        """Calls correct callback method for PydraMessages received over zmq.

        Parameters
        ----------
        tag : bytes
            Byte string encoding message tag.
        source : bytes
            Byte string encoding source of message.
        timestamp : bytes
            Bytes encoding the time the message was sent (float)
        flags : bytes
            Byte string encoding additional message flags.
        msg : iterable
            Iterable of message parts

        Raises
        ------
        TypeError if call signature of the callback method doesn't match output of PydraMessage.
        """
        tag, source, timestamp, flags, msg = PydraMessage.read_message(tag, source, timestamp, flags, *msg)
        try:  # get the appropriate callback method
            callback = self.msg_callbacks[tag]
        except KeyError:
            warnings.warn(f"{self.name} received a {tag} message from {source} but has no handler.")
            return
        try:  # try to call the callback method
            callback(self, tag, source, timestamp, flags, msg)
        except TypeError:  # raised if call signature of callback doesn't match message type
            raise TypeError(f"Call signature of {callback} in {self.name} does not match output of {tag} messages.")
        except Exception as err:
            message = traceback.format_exc()
            self.raise_error(err, message)

    def receive_messages(self, timeout: int = 0):
        """Polls for new messages from all subscriptions and passes them to appropriate handlers.

        Parameters
        ----------
        timeout : int
            Block for this duration (in milliseconds) until a message is received.
        """
        for tag, source, timestamp, flags, *msg in self.poll(timeout):
            self._handle_message(tag, source, timestamp, flags, msg)

    @EXIT.CALLBACK
    def handle_exit(self, **kwargs):
        """Callback for EXIT message."""
        self.exit()

    @STRING.CALLBACK
    def handle_string(self, s: str, **kwargs):
        """Callback for STRING messages."""
        self.recv_str(s, **kwargs)

    def recv_str(self, s: str, **kwargs):
        """Handles strings received over pydra network. May be re-implemented in subclasses.

        Parameters
        ----------
        s : str

        Other Parameters
        ----------------
        tag : str
            Message tag.
        source : str
            Source of the message.
        timestamp : float
            Time the message was sent.
        flags : str
            Additional flags received along with the message.
        """
        print(f"{self.name} received message from {kwargs['source']} at {kwargs['timestamp']}:\n{s}")

    @TRIGGER.CALLBACK
    def handle_trigger(self, **kwargs):
        """Callback for TRIGGER messages."""
        self.recv_trigger(kwargs["source"], kwargs["timestamp"])

    def recv_trigger(self, source: str, t: float):
        """Handles triggers received over pydra network. May be re-implemented in subclasses.

        Parameters
        ----------
        source : str
            Source of the trigger.
        t : float
            Time the trigger was sent.
        """
        print(f"{self.name} received trigger from {source} at {t}.")

    @EVENT.CALLBACK
    def handle_event(self, event_name: str, event_kw: dict, **kwargs):
        """Callback for EVENT messages. Calls the appropriate event callback method.

        Parameters
        ----------
        event_name : str
            Name of the event.
        event_kw : dict
            Keyword, value pairs for the associated event. Passed with ** to the event callback method.

        Other Parameters
        ----------------
        tag : str
            Message tag.
        source : str
            Source of the message.
        timestamp : float
            Time the message was sent.
        flags : str
            Additional flags received along with the message.
        """
        if event_name in self.event_callbacks:
            f = self.event_callbacks[event_name]
        else:
            try:
                f = self.__getattribute__(event_name)
            except AttributeError:
                return
        event_kw.update(**kwargs)
        f(**event_kw)

    @DATA.CALLBACK
    def handle_data(self, *args, **kwargs):
        """Callback for DATA messages."""
        self.recv_data(*args, **kwargs)

    @TIMESTAMPED.CALLBACK
    def handle_timestamped(self, *args, **kwargs):
        """Callback for DATA messages."""
        self.recv_timestamped(*args, **kwargs)

    @INDEXED.CALLBACK
    def handle_indexed(self, *args, **kwargs):
        """Callback for DATA messages."""
        self.recv_indexed(*args, **kwargs)

    @ARRAY.CALLBACK
    def handle_array(self, *args, **kwargs):
        """Callback for DATA messages."""
        self.recv_array(*args, **kwargs)

    @FRAME.CALLBACK
    def handle_frame(self, *args, **kwargs):
        """Callback for DATA messages."""
        self.recv_frame(*args, **kwargs)

    def recv_data(self, *args, **kwargs):
        """Handles generic data messages received over pydra network. May be re-implemented in subclasses."""
        pass

    def recv_timestamped(self, t: float, data: dict, **kwargs):
        """Handles timestamped data messages received over pydra network. May be re-implemented in
        subclasses.

        Parameters
        ----------
        t : float
        data : dict

        Other Parameters
        ----------------
        tag : str
            Message tag.
        source : str
            Source of the message.
        timestamp : float
            Time the message was sent.
        flags : str
            Additional flags received along with the message.
        """
        pass

    def recv_indexed(self, i: int, t: float, data: dict, **kwargs):
        """Handles indexed data messages received over pydra network. May be re-implemented in subclasses.

        Parameters
        ----------
        i : int
        t : float
        data : dict

        Other Parameters
        ----------------
        tag : str
            Message tag.
        source : str
            Source of the message.
        timestamp : float
            Time the message was sent.
        flags : str
            Additional flags received along with the message.
        """
        pass

    def recv_array(self, i: int, t: float, a: np.ndarray, **kwargs):
        """Handles array data messages received over pydra network. May be re-implemented in subclasses.

        Parameters
        ----------
        i : int
        t : float
        a : np.ndarray

        Other Parameters
        ----------------
        tag : str
            Message tag.
        source : str
            Source of the message.
        timestamp : float
            Time the message was sent.
        flags : str
            Additional flags received along with the message.
        """
        pass

    def recv_frame(self, i: int, t: float, frame: np.ndarray, **kwargs):
        """Handles frame data messages received over pydra network. May be re-implemented in subclasses.

        Parameters
        ----------
        i : int
        t : float
        frame : np.ndarray

        Other Parameters
        ----------------
        tag : str
            Message tag.
        source : str
            Source of the message.
        timestamp : float
            Time the message was sent.
        flags : str
            Additional flags received along with the message.
        """
        pass
