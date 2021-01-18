from ..base import PydraObject
from ..process import ProcessMixIn
from ..messaging import *
from ..messaging.serializers import *
from .threading import ThreadGroup
import zmq


class Saver(PydraObject, ProcessMixIn):

    name = "saver"

    @classmethod
    def configure(cls, zmq_config, ports, subscriptions=()):
        # Create dictionary for storing config info
        zmq_config[cls.name] = {}
        try:
            # Add subscriptions to config
            zmq_config[cls.name]["subscriptions"] = []
            # Add subscription to main pydra process
            subscribe_to_main = ("pydra", zmq_config["pydra"]["publisher"][1], (ExitMessage, EventMessage, LoggedMessage))
            zmq_config[cls.name]["subscriptions"].append(subscribe_to_main)
            for (name, save) in subscriptions:
                if name in zmq_config:
                    port = zmq_config[name]["publisher"][1]
                    messages = [TextMessage, LoggedMessage]
                    if save:
                        messages.append(DataMessage)
                    zmq_config[cls.name]["subscriptions"].append((name, port, tuple(messages)))
            # Add server for pydra client
            zmq_config[cls.name]["sender"] = zmq_config["pydra"]["receiver"]
        except KeyError:
            print(f"Cannot configure {cls.name}. Check zmq_configuration.")

    def __init__(self, groups, video_params, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.msg_handlers["log"] = self.handle_log
        # Message cache
        self.messages = []
        # Log
        self.log = []
        # Worker events
        self.worker_events = []
        # Query events
        self.events["query"] = self._query_event
        self.events["query_messages"] = self.query_messages
        self.events["query_data"] = self.query_data
        self.events["query_log"] = self.query_log
        self.events["query_events"] = self.query_events
        # Recording
        self.events["start_recording"] = self.start_recording
        self.events["stop_recording"] = self.stop_recording
        self.recording = False
        # Groups
        self.groups = []
        self.targets = {}
        for name, members in groups.items():
            group = ThreadGroup(name, members)
            self.groups.append(group)
            for members in members:
                self.targets[members] = group
        # Video params
        self.video_params = video_params

    def setup(self):
        self.zmq_sender.send(b"")

    def _process(self):
        self._recv()

    def exit(self, *args, **kwargs):
        self.close()

    def _recv(self):
        self.poll()

    def _query_event(self, query_type, **kwargs):
        event_name = "query_" + query_type
        if event_name in self.events:
            self.events[event_name]()

    def handle_log(self, name, data, **kwargs):
        name, data = LOGGED.decode(name, data)
        timestamp = kwargs["timestamp"]
        source = kwargs["source"]
        self.recv_log(timestamp, source, name, data)

    def recv_message(self, s, **kwargs):
        self.messages.append((kwargs["source"], kwargs["timestamp"], s))

    def recv_log(self, timestamp, source, name, data):
        if ("event" in data) and data["event"]:
            self.worker_events.append((timestamp, source, name, data))
        self.log.append((timestamp, source, name, data))

    def recv_timestamped(self, t, data, **kwargs):
        self.targets[kwargs["source"]].update(kwargs["source"], "timestamped", t, data)
        if kwargs["save"] and self.recording:
            self.targets[kwargs["source"]].save_timestamped(kwargs["source"], t, data)
        return

    def recv_indexed(self, t, i, data, **kwargs):
        self.targets[kwargs["source"]].update(kwargs["source"], "indexed", t, i, data)
        if kwargs["save"] and self.recording:
            self.targets[kwargs["source"]].save_indexed(kwargs["source"], t, i, data)
        return

    def recv_frame(self, t, i, frame, **kwargs):
        self.targets[kwargs["source"]].update(kwargs["source"], "frame", t, i, frame)
        if kwargs["save"] and self.recording:
            self.targets[kwargs["source"]].save_frame(kwargs["source"], t, i, frame)
        return

    def query_messages(self):
        self.zmq_sender.send(b"", zmq.SNDMORE)
        while len(self.messages):
            source, t, m = self.messages.pop(0)
            d = {"source": source,
                 "timestamp": t,
                 "message": m}
            self.zmq_sender.send(serialize_dict(d), zmq.SNDMORE)
        self.zmq_sender.send(b"")

    def query_data(self):
        for group in self.groups:
            if group.frame:
                name = serialize_string(group.name)
                frame = group.frame
                data = group.flush()
                self.zmq_sender.send_multipart([name, frame, data], zmq.SNDMORE)
        self.zmq_sender.send_multipart([b""])
        return

    def query_log(self):
        for item in self.log:
            serialized = LOGINFO.encode(*item)
            self.zmq_sender.send_multipart(serialized, zmq.SNDMORE)
        self.zmq_sender.send_multipart([b""])
        return

    def query_events(self):
        for event in self.worker_events:
            serialized = LOGINFO.encode(*event)
            self.zmq_sender.send_multipart(serialized, zmq.SNDMORE)
        self.zmq_sender.send_multipart([b""])
        self.worker_events = []
        return

    def start_recording(self, directory: str = None, filename: str = None, **kwargs):
        for group in self.groups:
            group.start(directory, filename)
        # Set recording to True
        self.recording = True
        return

    def stop_recording(self, **kwargs):
        # Stop all saving groups
        for group in self.groups:
            group.stop()
        # Set recording to False
        self.recording = False
        return
