from ..messaging import PydraMessage
import zmq

__all__ = ("ZMQSender", "ZMQPublisher", "ZMQReceiver", "ZMQSubscriber", "ZMQPoller")


class ZMQProxy:
    """Proxy class for handling interfaces between Pydra objects using zmq. Abstract base class. Children specify a zmq
    socket type as a class attribute which is used to instantiate the socket in __init__.

    Attributes
    ----------
    socket : zmq.Socket
        The zmq socket object for sending or receiving messages.
    """

    SOCKTYPE = -1

    def __init__(self):
        self.socket = self.context.socket(self.SOCKTYPE)

    @property
    def context(self) -> zmq.Context:
        """Property that return the zmq context for convenience."""
        return zmq.Context.instance()


class ZMQSender(ZMQProxy):
    """For sending messages one-to-one.

    Parameters
    ----------
    port : str
        The address where messages are sent.
    """

    SOCKTYPE = zmq.PUSH

    def __init__(self, port):
        super().__init__()
        self.port = port
        self.socket.bind(self.port)


class ZMQPublisher(ZMQSender):
    """For sending messages one-to-many."""

    SOCKTYPE = zmq.PUB


class ZMQReceiver(ZMQProxy):
    """For receiving messages one-to-one.

    Parameters
    ----------
    port : str
        The address where messages are received.
    """

    SOCKTYPE = zmq.PULL

    def __init__(self, port):
        super().__init__()
        self.port = port
        self.socket.connect(self.port)


class ZMQSubscriber(ZMQProxy):
    """For receiving messages many-to-one."""

    SOCKTYPE = zmq.SUB

    def add_connection(self, port, messages=()):
        """Adds a new connection for subscribing to messages.

        Parameters
        ----------
        port : str
            The address where messages are received.
        messages : iterable
            Iterable of PydraMessage objects that the subscriber should listen for.
        """
        self.socket.connect(port)
        for message in messages:
            self.socket.setsockopt(zmq.SUBSCRIBE, message.flag)


class ZMQPoller:
    """Container class for managing subscriptions to many channels. Polling the subscription manager yields parsed Pydra
    messages received since the last time the poll method was called.

    Attributes
    ----------
    poller : zmq.Poller
        A zmq poller object for handling subscriptions to multiple channels.
    subscriptions : tuple

    """

    def __init__(self, subscriptions=(), receivers=()):
        self.poller = zmq.Poller()
        self._sockets = {}
        for (name, port, messages) in subscriptions:
            self.add_subscription(name, port, messages)
        for (name, port) in receivers:
            self.add_receiver(name, port)

    def add_subscription(self, name, port, messages):
        """Adds a new subscription.

        Parameters
        ----------
        name : str
            The name of the Pydra object being subscribed to.
        port : str
            The address where new messages are received.
        messages : iterable
            Iterable of PydraMessage objects that should be listened for on the given port.
        """
        subscriber = ZMQSubscriber()
        subscriber.add_connection(port, messages)
        self.poller.register(subscriber.socket, zmq.POLLIN)
        self._sockets[name] = subscriber

    def add_receiver(self, name, port):
        receiver = ZMQReceiver(port)
        self.poller.register(receiver.socket, zmq.POLLIN)
        self._sockets[name] = receiver

    @property
    def sockets(self) -> set:
        """Returns the set of zmq sockets being subscribed to."""
        return {subscriber.socket for subscriber in self._sockets.values()}

    def poll(self):
        """Checks poller for new messages from all subscriptions.

        Yields
        ------
        flag, source, timestamp, other, args
        """
        events = dict(self.poller.poll(0))
        for sock in events:
            if sock in self.sockets:
                flag, source, timestamp, other, args = PydraMessage.recv(sock)
                yield flag, source, timestamp, other, args
