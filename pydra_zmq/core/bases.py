import zmq
from .messaging import *


class ZMQContext:

    name = ""

    @classmethod
    def configure(cls, zmq_config, ports):
        zmq_config[cls.name] = {}

    def __init__(self, zmq_config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get the zmq configuration
        self.zmq_config = zmq_config[self.name]
        # Create the zmq context and bindings
        self.zmq_context = zmq.Context.instance()
        if "publisher" in self.zmq_config:
            self._zmq_set_publisher()
        if "subscriptions" in self.zmq_config:
            self._zmq_set_subscriptions()
        if "client" in self.zmq_config:
            self._zmq_set_client()
        if "server" in self.zmq_config:
            self._zmq_set_server()
        # Set data handlers
        self.msg_handlers = {
            "exit": self.close,
            "message": self.handle_message,
            "event": self.handle_event,
            "data": self.handle_data
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

    def _zmq_set_client(self):
        self.zmq_client = self.zmq_context.socket(zmq.REQ)
        try:
            self.zmq_client.connect(self.zmq_config["client"][1])
        except KeyError:
            print(f"No req-rep pair specified in zmq_config file of {self.name}")

    def _zmq_set_server(self):
        self.zmq_server = self.zmq_context.socket(zmq.REP)
        try:
            self.zmq_server.bind(self.zmq_config["server"][0])
        except KeyError:
            print(f"No req-rep pair specified in zmq_config file of {self.name}")

    def _destroy(self):
        self.zmq_context.destroy(200)

    def _handle_subscriptions(self):
        sockets = dict(self.zmq_poller.poll(0))
        for name, sock in self.zmq_subscriptions.items():
            if sock in sockets:
                flag, source, timestamp, dtypes, args = ZMQMessage.recv(sock)
                self.msg_handlers[flag](*args, flag=flag, source=source, timestamp=timestamp, dtypes=dtypes)

    @MESSAGE()
    def send_message(self, s):
        return s

    def handle_message(self, s, **kwargs):
        s = MESSAGE().decode(s)
        self.recv_message(s, **kwargs)

    def recv_message(self, s, **kwargs):
        print(f"{self.name} received from {kwargs.get('source', 'UNKNOWN')} at {kwargs.get('timestamp', 0.0)}:\n{s}")

    def close(self, *args, **kwargs):
        return

    @EVENT()
    def send_event(self, event_name, **kwargs):
        return event_name, kwargs

    def handle_event(self, event_name, event_kw, **kwargs):
        event_name, event_kw = EVENT().decode(event_name, event_kw)
        if event_name in self.events:
            event_kw.update(**kwargs)
            ret = self.events[event_name](**event_kw)
            return ret

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
        flags = kwargs["dtypes"]
        if "s" in flags:
            kwargs["save"] = True
        if "t" in flags:
            self.recv_timestamped(*data, **kwargs)
        elif "i" in flags:
            self.recv_indexed(*data, **kwargs)
        elif "f" in flags:
            self.recv_frame(*data, **kwargs)

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
        zmq_config[cls.name] = {}
        try:
            # Add a port for publishing outputs
            zmq_config[cls.name]["publisher"] = ports.pop(0)
            # Add client
            zmq_config[cls.name]["client"] = ports.pop(0)
        except IndexError:
            print(f"Not enough ports to configure {cls.name}")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @EXIT()
    def exit(self):
        return ()

    # def receive_messages(self):
    #     # Handle messages
    #     messages = []
    #     while True:
    #         self.zmq_client.send_multipart([b"message"])
    #         message = self.zmq_client.recv_multipart()
    #         if message[0]:
    #             messages.append(message)
    #         else:
    #             break
    #     return messages

    # def receive_event(self, source, event_name):
    #     source = io.serialize_string(source)
    #     event_name = io.serialize_string(event_name)
    #     self.zmq_client.send_multipart([b"event", source, event_name])
    #     ret = self.zmq_client.recv_multipart()
    #     return ret

    # def send_event(self, event_name, source=None, wait=True, **event_kw):
    #     if wait and source:
    #         super().send_event(event_name, **event_kw)
    #         ret = self.receive_event(source, event_name)
    #         return io.deserialize_int(ret[0])
    #     else:
    #         super().send_event(event_name, **event_kw)


class ZMQSaver(ZMQContext):

    @classmethod
    def configure(cls, zmq_config, ports, subscriptions=()):
        # Create dictionary for storing config info
        zmq_config[cls.name] = {}
        try:
            # Add subscriptions to config
            zmq_config[cls.name]["subscriptions"] = []
            # Add subscription to main pydra process
            subscribe_to_main = ("pydra", zmq_config["pydra"]["publisher"][1], (EXIT, EVENT))
            zmq_config[cls.name]["subscriptions"].append(subscribe_to_main)
            for (name, save) in subscriptions:
                if name in zmq_config:
                    port = zmq_config[name]["publisher"][1]
                    messages = [MESSAGE, DATA]
                    zmq_config[cls.name]["subscriptions"].append((name, port, tuple(messages)))
            # Add server for pydra client
            zmq_config[cls.name]["server"] = zmq_config["pydra"]["client"]
        except KeyError:
            print(f"Cannot configure {cls.name}. Check zmq_configuration.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message_cache = []
        self.event_cache = {}
        # self.server_handlers = {
        #     "message": self.reply_messages,
        #     "event": self.reply_event,
        #     "data": self.reply_data
        # }
        self.events["log_event"] = self.log_event
        self.save_from = []
        for name, port, messages in self.zmq_config["subscriptions"]:
            if DATA in messages:
                self.save_from.append(name)

    def _recv(self):
        # if self._handle_server():
        #     return 1
        return self._handle_subscriptions()

    # def _handle_server(self):
    #     if self.zmq_server.poll(0):
    #         msg_flag, *args = self.zmq_server.recv_multipart()
    #         msg_flag = io.deserialize_string(msg_flag)
    #         return self.server_handlers[msg_flag](*args)

    def recv_message(self, s, **kwargs):
        self.message_cache.append((kwargs["source"], kwargs["timestamp"], s))

    # def handle_event(self, event_name, event_kw, **kwargs):
    #     ret = super().handle_event(event_name, event_kw, **kwargs)
    #     event_name = io.deserialize_string(event_name)
    #     self.log_event(event_name, ret, **kwargs)

    def log_event(self, event_name, ret, **kwargs):
        print(event_name, ret, kwargs)
        if kwargs["source"] in self.event_cache:
            self.event_cache[kwargs["source"]][event_name] = ret
        else:
            self.event_cache[kwargs["source"]] = {event_name: ret}

    # def reply_messages(self, *args):
    #     while len(self.message_cache):
    #         source, timestamp, message = self.message_cache.pop(0)
    #         out = io.serialize_string(source), io.serialize_float(timestamp), message
    #         self.zmq_server.send_multipart(out)
    #     self.zmq_server.send_multipart([b""])

    # def reply_event(self, source, event_name):
    #     source = io.deserialize_string(source)
    #     event_name = io.deserialize_string(event_name)
    #     while True:
    #         if (source in self.event_cache) and (event_name in self.event_cache[source]):
    #             ret = self.event_cache[source][event_name]
    #             ret_bytes = io.serialize_int(int(ret))
    #             self.zmq_server.send_multipart([ret_bytes])
    #             del self.event_cache[source][event_name]
    #             break
    #         else:
    #             ret = self._handle_subscriptions()
    #             if ret:
    #                 return

    def reply_data(self, *args):
        pass


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

    def _recv(self):
        return self._handle_subscriptions()
