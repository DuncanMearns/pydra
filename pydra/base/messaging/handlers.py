"""
Module containing the ZMQProxy and associated classes for sending and receiving to pydra messages.
"""
from .messaging import PydraMessage

import zmq
from typing import Iterable, List

__all__ = ("ZMQPublisher", "ZMQPoller")


class ZMQProxy:
    """Proxy class for handling interfaces between Pydra objects using zmq. Abstract base class. Children specify a zmq
    socket type as a class attribute which is used to instantiate the socket in __init__.

    Parameters
    ----------
    address : str
        A tcp address.

    Attributes
    ----------
    socket : zmq.Socket
        The zmq socket object for sending or receiving messages.
    """

    sock_type = None
    connect_function = None

    def __init__(self, address: str):
        self.socket = self.context.socket(self.sock_type)
        self.address = address
        self.connect_function(self.socket, self.address)

    @property
    def context(self) -> zmq.Context:
        """Property that return the zmq context for convenience."""
        return zmq.Context.instance()

    def send(self, *msg_parts: bytes):
        """Send a multipart message over the socket."""
        self.socket.send_multipart(msg_parts)

    def recv(self) -> Iterable[bytes]:
        """Receive a multipart message from the socket."""
        if self.socket.poll(0):
            return self.socket.recv_multipart()
        return ()

    def recv_multi(self) -> Iterable[list]:
        """Receive all messages queued on the socket."""
        msgs = []
        while self.socket.poll(0):
            msg = self.socket.recv_multipart()
            msgs.append(msg)
        return msgs


def connect(socket, addr):
    """Connect a socket to an address."""
    socket.connect(addr)


def bind(socket, addr):
    """Bind a socket to an address."""
    socket.bind(addr)


class ZMQPublisher(ZMQProxy):
    """For sending messages one-to-many."""

    sock_type = zmq.PUB
    connect_function = staticmethod(bind)


class ZMQSubscriber(ZMQProxy):
    """For receiving messages."""

    sock_type = zmq.SUB
    connect_function = staticmethod(connect)

    def subscribe(self, messages: Iterable[PydraMessage]):
        """Adds a new connection for subscribing to messages.

        Parameters
        ----------
        messages : iterable
            Iterable of PydraMessage objects that the subscriber should listen for.
        """
        for message in messages:
            self.socket.setsockopt_string(zmq.SUBSCRIBE, message.tag)


class ZMQPoller:
    """Class for managing subscriptions to many channels."""

    def __init__(self, subscriptions: Iterable[Iterable] = ()):
        self.poller = zmq.Poller()
        self.subscribers = {}
        for (name, addr, messages) in subscriptions:
            self.add_subscription(name, addr, messages)

    def add_subscription(self, name: str, addr: str, messages: Iterable[PydraMessage]):
        """Adds a new subscription.

        Parameters
        ----------
        name : str
            The name of the Pydra object being subscribed to.
        addr : str
            The address where new messages are received.
        messages : iterable
            Iterable of PydraMessage objects that should be listened for on the given port.
        """
        subscriber = ZMQSubscriber(addr)
        subscriber.subscribe(messages)
        self.poller.register(subscriber.socket, zmq.POLLIN)
        self.subscribers[name] = subscriber

    @property
    def inverse_lookup(self):
        """Allows a socket to be accessed given the name of the corresponding publisher."""
        return dict([(subscriber.socket, name) for name, subscriber in self.subscribers.items()])

    def poll(self, timeout=0) -> List[list]:
        """Checks poller for new messages from all subscriptions.

        Parameters
        ----------
        timeout : int
            Get all messages received within the timeout time (ms).

        Returns
        ------
        flag, source, timestamp, other, args
        """
        get_subscriber = self.inverse_lookup
        events = dict(self.poller.poll(timeout))
        msgs = []
        for sock in events:
            name = get_subscriber[sock]
            new = self.subscribers[name].recv_multi()
            msgs.extend(new)
        return msgs
