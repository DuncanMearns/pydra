import zmq
from multiprocessing import Process
from .messaging import *


class ZMQContext:

    name = ""

    @classmethod
    def configure(cls, zmq_config, ports):
        if cls.name not in zmq_config:
            zmq_config[cls.name] = {}

    def __init__(self, zmq_config=None, *args, **kwargs):
        super().__init__()
        # Get the zmq configuration
        self.zmq_config = zmq_config[self.name]
        # Create the zmq context and bindings
        self.zmq_context = zmq.Context.instance()
        if "publisher" in self.zmq_config:
            self._zmq_set_publisher()
        if "subscriptions" in self.zmq_config:
            self._zmq_set_subscriptions()
        if "receiver" in self.zmq_config:
            self._zmq_set_receiver()
        if "sender" in self.zmq_config:
            self._zmq_set_sender()
        # Set data handlers
        self.msg_handlers = {
            "exit": self.exit,
            "message": self.handle_message,
            "event": self.handle_event,
            "data": self.handle_data,
            "log": self.handle_log,
            "trigger": self.send_trigger
        }
        # Create events
        self.events = {}

    def _zmq_set_publisher(self):
        """Create the publisher for sending messages"""
        self.zmq_publisher = self.zmq_context.socket(zmq.PUB)
        try:
            self.zmq_publisher.bind(self.zmq_config["publisher"][0])
        except KeyError:
            print(f"No publisher specified in zmq_config file of {self.name}")

    def _zmq_set_remote(self):
        self.zmq_remote = self.zmq_context.socket(zmq.REQ)
        try:
            self.zmq_remote.connect(self.zmq_config["remote"])
        except KeyError:
            print(f"No remote port specified in zmq_config file of {self.name}")

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

    def _zmq_set_receiver(self):
        self.zmq_receiver = self.zmq_context.socket(zmq.PULL)
        try:
            self.zmq_receiver.bind(self.zmq_config["receiver"][0])
        except KeyError:
            print(f"No sender-receiver pair specified in zmq_config file of {self.name}")

    def _zmq_set_sender(self):
        self.zmq_sender = self.zmq_context.socket(zmq.PUSH)
        try:
            self.zmq_sender.connect(self.zmq_config["sender"][1])
        except KeyError:
            print(f"No sender-receiver pair specified in zmq_config file of {self.name}")

    def _destroy(self):
        self.zmq_context.destroy(200)

    def poll(self):
        sockets = dict(self.zmq_poller.poll(0))
        for name, sock in self.zmq_subscriptions.items():
            if sock in sockets:
                msg, source, timestamp, flags, args = ZMQMessage.recv(sock)
                self.msg_handlers[msg](*args, msg=msg, source=source, timestamp=timestamp, flags=flags)

    @message
    def send_message(self, s):
        return s

    def handle_message(self, s, **kwargs):
        s = message.decode(s)
        self.recv_message(s, **kwargs)

    def recv_message(self, s, **kwargs):
        print(f"{self.name} received from {kwargs.get('source', 'UNKNOWN')} at {kwargs.get('timestamp', 0.0)}:\n{s}")

    def exit(self, *args, **kwargs):
        return

    @TRIGGER()
    def send_trigger(self, *args, **kwargs):
        return ()

    @event
    def send_event(self, event_name, **kwargs):
        return event_name, kwargs

    def handle_event(self, event_name, event_kw, **kwargs):
        event_name, event_kw = event.decode(event_name, event_kw)
        if event_name in self.events:
            event_kw.update(**kwargs)
            self.events[event_name](**event_kw)

    def handle_log(self, name, data, **kwargs):
        name, data = logged.decode(name, data)
        timestamp = kwargs["timestamp"]
        source = kwargs["source"]
        self.recv_log(timestamp, source, name, data)

    def recv_log(self, timestamp, source, name, data):
        return

    @DATA(TIMESTAMPED)
    def send_timestamped(self, t, data):
        return t, data

    @DATA(INDEXED)
    def send_indexed(self, t, i, data):
        return t, i, data

    @DATA(FRAME)
    def send_frame(self, t, i, frame):
        return t, i, frame

    def handle_data(self, *data, **kwargs):
        flags = kwargs["flags"]
        if "s" in flags:
            kwargs["save"] = True
        if "t" in flags:
            self.recv_timestamped(*data, **kwargs)
        elif "i" in flags:
            self.recv_indexed(*data, **kwargs)
        elif "f" in flags:
            self.recv_frame(*data, **kwargs)

    def send_remote(self, *args):
        dtypes = [type(arg) for arg in args]
        serialized = ZMQMessage(*dtypes).encode(*args)
        self.zmq_remote.send_multipart(serialized)
        ret = self.zmq_remote.recv()
        return ret

    def recv_timestamped(self, t, data, **kwargs):
        return

    def recv_indexed(self, t, i, data, **kwargs):
        return

    def recv_frame(self, t, i, frame, **kwargs):
        return


class ZMQMain(ZMQContext):

    @classmethod
    def configure(cls, zmq_config, ports):
        # Create dictionary for storing config info
        if cls.name not in zmq_config:
            zmq_config[cls.name] = {}
        try:
            # Add a port for publishing outputs
            if "publisher" not in zmq_config[cls.name]:
                zmq_config[cls.name]["publisher"] = ports.pop(0)
            # Add client
            zmq_config[cls.name]["receiver"] = ports.pop(0)
        except IndexError:
            print(f"Not enough ports to configure {cls.name}")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @EXIT()
    def exit(self):
        return ()

    def query(self, query_type):
        self.send_event("query", query_type=query_type)
        result = self.zmq_receiver.recv_multipart()
        return result


class ZMQSaver(ZMQContext):

    @classmethod
    def configure(cls, zmq_config, ports, subscriptions=()):
        # Create dictionary for storing config info
        zmq_config[cls.name] = {}
        try:
            # Add subscriptions to config
            zmq_config[cls.name]["subscriptions"] = []
            # Add subscription to main pydra process
            subscribe_to_main = ("pydra", zmq_config["pydra"]["publisher"][1], (EXIT, EVENT, LOGGED))
            zmq_config[cls.name]["subscriptions"].append(subscribe_to_main)
            for (name, save) in subscriptions:
                if name in zmq_config:
                    port = zmq_config[name]["publisher"][1]
                    messages = [MESSAGE, LOGGED]
                    if save:
                        messages.append(DATA)
                    zmq_config[cls.name]["subscriptions"].append((name, port, tuple(messages)))
            # Add server for pydra client
            zmq_config[cls.name]["sender"] = zmq_config["pydra"]["receiver"]
        except KeyError:
            print(f"Cannot configure {cls.name}. Check zmq_configuration.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events["query"] = self._query_event

    def _recv(self):
        self.poll()

    def _query_event(self, query_type, **kwargs):
        event_name = "query_" + query_type
        if event_name in self.events:
            self.events[event_name]()


class ZMQWorker(ZMQContext):

    @classmethod
    def configure(cls, zmq_config, ports, subscriptions=()):
        # Create dictionary for storing config info
        if cls.name not in zmq_config:
            zmq_config[cls.name] = {}
        try:
            # Add a port for publishing outputs
            if "publisher" not in zmq_config[cls.name]:
                zmq_config[cls.name]["publisher"] = ports.pop(0)
            # Add subscriptions to config
            zmq_config[cls.name]["subscriptions"] = []
            # Add subscription to main pydra process
            subscribe_to_main = ("pydra", zmq_config["pydra"]["publisher"][1], (EVENT, EXIT))
            zmq_config[cls.name]["subscriptions"].append(subscribe_to_main)
            for name, port, messages in subscriptions:
                if name in zmq_config:
                    port = zmq_config[name]["publisher"][1]
                zmq_config[cls.name]["subscriptions"].append((name, port, messages))
        except IndexError:
            print(f"Not enough ports to configure {cls.name}")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events["test_connection"] = self.test_connection

    @logged
    def test_connection(self, **kwargs):
        return dict()

    def _recv(self):
        self.poll()


class PydraProcess(Process):

    def __init__(self, worker, worker_args, worker_kwargs, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.worker_type = worker
        self.worker_args = worker_args
        self.worker_kwargs = worker_kwargs

    def run(self):
        self.worker = self.worker_type(*self.worker_args, **self.worker_kwargs)
        self.worker.run()


class ProcessMixIn:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exit_flag = 0

    @classmethod
    def start(cls, *args, **kwargs):
        process = PydraProcess(cls, args, kwargs)
        process.start()

    def close(self):
        self.exit_flag = 1

    def setup(self):
        return

    def _process(self):
        return

    def run(self):
        self.setup()
        while not self.exit_flag:
            self._process()


class Worker(ZMQWorker, ProcessMixIn):

    name = "worker"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _process(self):
        self._recv()

    def exit(self, *args, **kwargs):
        self.close()


class Acquisition(Worker):

    name = "acquisition"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _process(self):
        self._recv()
        self.acquire()

    def acquire(self):
        return


class RemoteWorker(Worker):

    name = "remote"

    @classmethod
    def configure(cls, zmq_config, ports, subscriptions=()):
        # Create dictionary for storing config info
        try:
            assert "remote" in zmq_config[cls.name]
        except AssertionError:
            raise ValueError(f"zmq_config for {cls.name} must contain a 'remote' key")
        super(RemoteWorker, cls).configure(zmq_config, ports, subscriptions)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
