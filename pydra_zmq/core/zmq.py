import zmq
from .serialize import _deserialize_string, _deserialize_float
from .messaging import MESSAGE, STATE, EXIT, DATA
from .messaging import OutputMessage as output


class ZMQContext:

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
        # Create states
        self.states = {}
        # Set data handlers
        self.msg_handlers = {
            "exit": self._close,
            "message": self._recv_message,
            "state": self._recv_state,
            "data": self._recv_data
        }

    @output(MESSAGE)
    def send_message(self, s):
        return s

    def _recv_message(self, s, **kwargs):
        s = MESSAGE.serializer().decode(s)
        self.recv_message(s, **kwargs)

    def recv_message(self, s, **kwargs):
        print(f"{self.name} received from {kwargs.get('source', 'UNKNOWN')} at {kwargs.get('timestamp', 0.0)}:\n{s}")

    @output(EXIT)
    def exit(self):
        return "EXIT", 1

    def close(self, **kwargs):
        return

    def _close(self, *args, **kwargs):
        self.close(**kwargs)
        return 1

    @output(STATE)
    def send_state(self, state, val):
        return state, val

    def _recv_state(self, state, val, **kwargs):
        state, val = STATE.serializer().decode(state, val)
        if state in self.states:
            self.states[state](val, **kwargs)

    @output(DATA, "t")
    def send_timestamped(self, t, data):
        return t, data

    def recv_timestamped(self, t, data, **kwargs):
        return

    @output(DATA, "i")
    def send_indexed(self, t, i, data):
        return t, i, data

    def recv_indexed(self, t, i, data, **kwargs):
        return

    @output(DATA, "f")
    def send_frame(self, t, i, frame):
        return t, i, frame

    def recv_frame(self, t, i, frame, **kwargs):
        return

    def _recv_data(self, *data, **kwargs):
        flag = kwargs["flags"]
        if flag == b"t":
            self.recv_timestamped(*data, **kwargs)
        elif flag == b"i":
            self.recv_indexed(*data, **kwargs)
        elif flag == b"f":
            self.recv_frame(*data, **kwargs)

    def _handle_event(self, msg_flag, source, t, flags, *parts):
        msg_flag = _deserialize_string(msg_flag)
        source = _deserialize_string(source)
        t = _deserialize_float(t)
        ret = self.msg_handlers[msg_flag](*parts, source=source, timestamp=t, flags=flags)
        return ret

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
        if name in self.zmq_subscriptions:
            for message in messages:
                self.zmq_subscriptions[name].setsockopt(zmq.SUBSCRIBE, message.flag)
        else:
            zmq_subscriber = self.zmq_context.socket(zmq.SUB)
            zmq_subscriber.connect(port)
            for message in messages:
                zmq_subscriber.setsockopt(zmq.SUBSCRIBE, message.flag)
            self.zmq_subscriptions[name] = zmq_subscriber
            self.zmq_poller.register(zmq_subscriber, zmq.POLLIN)


class ZMQMain(ZMQContext):

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


class ZMQWorker(ZMQContext):

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
