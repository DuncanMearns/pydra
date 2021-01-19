from ..base import PydraObject
from ..process import ProcessMixIn
from ..messaging import *
from ..messaging.serializers import *
from .threading import ThreadGroup
import zmq


class Saver(PydraObject, ProcessMixIn):

    name = "saver"

    def __init__(self, groups, video_params, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add log message handling
        self.msg_handlers["log"] = self.handle_log
        self.log = []
        # Create caches for storing worker messages and events
        self.worker_events = []
        self.messages = []
        # Add query events for direct communication with pydra
        self.events["query"] = self._query
        self.events["query_messages"] = self.query_messages
        self.events["query_log"] = self.query_log
        self.events["query_events"] = self.query_events
        self.events["query_data"] = self.query_data
        # Recording events
        self.events["start_recording"] = self.start_recording
        self.events["stop_recording"] = self.stop_recording
        self.recording = False
        # Groups
        self.groups = []
        self.targets = {}
        for name, members in groups.items():
            group = ThreadGroup(name, members)
            self.groups.append(group)
            for member in members:
                self.targets[member] = group
        # Video params
        self.video_params = video_params

    def setup(self):
        self.zmq_sender.send(b"")  # send empty byte to pydra

    def _process(self):
        """Receive messages from workers."""
        self.poll()

    def exit(self, *args, **kwargs):
        self.close()

    def handle_log(self, name, data, **kwargs):
        """Handles logged messages.

        The log is a list of messages sent within the pydra network. Each item in the log contains a timestamp when the
        message was sent, the source of the message, the name of the message, and the data contained within the message.
        """
        name, data = LOGGED.decode(name, data)
        timestamp = kwargs["timestamp"]
        source = kwargs["source"]
        if ("event" in data) and data["event"]:
            self.worker_events.append((timestamp, source, name, data))
        self.log.append((timestamp, source, name, data))

    def _query(self, query_type, **kwargs):
        """Handles any query events received from pydra."""
        event_name = "query_" + query_type
        if event_name in self.events:
            self.events[event_name]()

    def query_messages(self):
        """Fulfills a request from pydra for messages."""
        while len(self.messages):
            source, t, m = self.messages.pop(0)
            d = {"source": source,
                 "timestamp": t,
                 "message": m}
            self.zmq_sender.send(serialize_dict(d), zmq.SNDMORE)
        self.zmq_sender.send(b"")

    def query_log(self):
        """Fulfills a request from pydra for the log."""
        for item in self.log:
            serialized = INFO.encode(*item)
            self.zmq_sender.send_multipart(serialized, zmq.SNDMORE)
        self.zmq_sender.send_multipart([b""])

    def query_events(self):
        """Fulfills a request from pydra for worker events."""
        for event in self.worker_events:
            serialized = INFO.encode(*event)
            self.zmq_sender.send_multipart(serialized, zmq.SNDMORE)
        self.zmq_sender.send_multipart([b""])
        self.worker_events = []

    def query_data(self):
        """Fulfills a request from pydra for data."""
        for group in self.groups:
            if group.frame:
                name = serialize_string(group.name)
                frame = group.frame
                data = group.flush()
                self.zmq_sender.send_multipart([name, frame, data], zmq.SNDMORE)
        self.zmq_sender.send_multipart([b""])

    def recv_message(self, s, **kwargs):
        self.messages.append((kwargs["source"], kwargs["timestamp"], s))

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
