import zmq
from .messaging import MESSAGE, STATE, EXIT
from .messaging import OutputMessage as output


class ZMQ:

    name = ""

    @classmethod
    def configure(cls, zmq_config, ports):
        zmq_config[cls.name] = {}

    def __init__(self, zmq_config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get the zmq configuration
        self.zmq_config = zmq_config[self.name]
        # Create the zmq context
        self.zmq_context = zmq.Context.instance()

    @output(MESSAGE)
    def send_message(self, s):
        return s

    @output(STATE)
    def send_state(self, state, val):
        return state, val

    @output(EXIT)
    def exit(self):
        return "EXIT", 1

    def _zmq_set_publisher(self):
        """Create the publisher for sending messages"""
        self.zmq_publisher = self.zmq_context.socket(zmq.PUB)
        try:
            self.zmq_publisher.bind(self.zmq_config["publisher"][0])
        except KeyError:
            print(f"No publisher specified in zmq_config file of {self.name}")

    def _zmq_set_subscriptions(self):
        # Create a poller to check for messages on subscription channels
        self.zmq_poller = zmq.Poller()
        # Connect to each subscription channel
        self.zmq_subscriptions = {}
        try:
            for subscription in self.zmq_config["subscriptions"]:
                self._zmq_add_subscription(*subscription)
        except KeyError:
            pass

    def _zmq_add_subscription(self, name, port, messages):
        zmq_subscriber = self.zmq_context.socket(zmq.SUB)
        zmq_subscriber.connect(port)
        for message in messages:
            zmq_subscriber.setsockopt(zmq.SUBSCRIBE, message.flag)
        self.zmq_subscriptions[name] = zmq_subscriber
        self.zmq_poller.register(zmq_subscriber, zmq.POLLIN)


class ZMQMain(ZMQ):

    @classmethod
    def configure(cls, zmq_config, ports):
        # Create dictionary for storing config info
        zmq_config[cls.name] = {}
        try:
            # Add a port for publishing outputs
            zmq_config[cls.name]["publisher"] = ports.pop(0)
        except IndexError:
            print(f"Not enough ports to configure {cls.name}")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._zmq_set_publisher()


class ZMQWorker(ZMQ):

    @classmethod
    def configure(cls, zmq_config, ports, subscriptions=()):
        # Create dictionary for storing config info
        zmq_config[cls.name] = {}
        try:
            # Add a port for publishing outputs
            zmq_config[cls.name]["publisher"] = ports.pop(0)
            # Add subscriptions to config
            zmq_config[cls.name]["subscriptions"] = []
            # Add subscription to main pydra process
            subscribe_to_main = ("pydra", zmq_config["pydra"]["publisher"][1], (MESSAGE, STATE, EXIT))
            zmq_config[cls.name]["subscriptions"].append(subscribe_to_main)
            for name, port, messages in subscriptions:
                if name in zmq_config:
                    port = zmq_config[name]["publisher"][1]
                zmq_config[cls.name]["subscriptions"].append((name, port, messages))
        except IndexError:
            print(f"Not enough ports to configure {cls.name}")
        return ports

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._zmq_set_publisher()
        self._zmq_set_subscriptions()
