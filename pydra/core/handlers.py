from .messaging import PydraMessage
import zmq

__all__ = ("ZMQSender", "ZMQPublisher", "ZMQReceiver", "ZMQSubscriber", "SubscriptionManager")


class ZMQProxy:

    SOCKTYPE = -1

    def __init__(self):
        self.socket = self.context.socket(self.SOCKTYPE)

    @property
    def context(self):
        return zmq.Context.instance()


class ZMQSender(ZMQProxy):

    SOCKTYPE = zmq.PUSH

    def __init__(self, port):
        super().__init__()
        self.port = port
        self.socket.bind(self.port)


class ZMQPublisher(ZMQSender):

    SOCKTYPE = zmq.PUB


class ZMQReceiver(ZMQProxy):

    SOCKTYPE = zmq.PULL

    def __init__(self, port):
        super().__init__()
        self.port = port
        self.socket.connect(self.port)


class ZMQSubscriber(ZMQProxy):

    SOCKTYPE = zmq.SUB

    def add_connection(self, port, messages=()):
        self.socket.connect(port)
        for message in messages:
            self.socket.setsockopt(zmq.SUBSCRIBE, message.flag)


class SubscriptionManager:

    def __init__(self, *subscriptions):
        self.poller = zmq.Poller()
        self.subscriptions = {}
        for (name, port, messages) in subscriptions:
            self.add_subscription(name, port, messages)

    def add_subscription(self, name, port, messages):
        subscriber = ZMQSubscriber()
        subscriber.add_connection(port, messages)
        self.poller.register(subscriber.socket, zmq.POLLIN)
        self.subscriptions[name] = subscriber

    @property
    def sockets(self):
        return {subscriber.socket for subscriber in self.subscriptions.values()}

    def poll(self):
        """Checks for poller for new messages from all subscriptions."""
        events = dict(self.poller.poll(0))
        for sock, event_flag in events:
            if sock in self.sockets:
                flag, source, timestamp, other, args = PydraMessage.recv(sock)
                yield flag, source, timestamp, other, args
