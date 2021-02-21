from pydra.core.base import PydraObject
from pydra.core.process import ProcessMixIn
from pydra.core.messaging import *
from pydra.core.messaging.serializers import *
from .threading import PipelineSaver
import zmq


class Saver(PydraObject, ProcessMixIn):
    """Singleton Saver class that integrates and handles incoming messages from all workers.

    Parameters
    ----------
    pipelines : dict
        Dictionary of workers (as a list of names) assigned to each pipeline (keys). Passed from pydra pipelines
        property.

    Attributes
    ----------
    log : list
        Logged messages from all pydra objects.
    worker_events : list
        Copy of events that workers have received.
    messages : list
        List of messages received from all pydra objects.
    recording : bool
        Stores whether data are currently being recorded and saved.
    savers : list
        List that stores all PipelineSaver objects.
    targets : dict
        A dictionary that maps data received from workers to the appropriate PipelineSaver object.
    """

    name = "saver"

    def __init__(self, pipelines: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add log message handling
        self.msg_handlers["log"] = self.handle_log
        # Create caches for storing worker messages and events
        self.event_log = []
        self.messages = []
        # Add query events for direct communication with pydra
        self.events["query"] = self._query
        self.events["query_messages"] = self.query_messages
        self.events["query_events"] = self.query_events
        self.events["query_data"] = self.query_data
        # Recording events
        self.events["start_recording"] = self.start_recording
        self.events["stop_recording"] = self.stop_recording
        self.recording = False
        # Create pipelines for handling data
        self.savers = []
        self.targets = {}
        for name, members in pipelines.items():
            saver = PipelineSaver(name, members)
            self.savers.append(saver)
            for member in members:
                self.targets[member.name] = saver

    def setup(self):
        """Sends an empty byte to pydra"""
        self.zmq_sender.send(b"")

    def _process(self):
        """Receive messages from workers."""
        self.poll()

    def exit(self, *args, **kwargs):
        """Terminates the process loop."""
        if self.recording:
            self.stop_recording()
        self.close()

    def handle_log(self, name, data, **kwargs):
        """Handles logged messages.

        The log is a list of messages sent within the pydra network. Each item in the log contains a timestamp when the
        message was sent, the source of the message, the name of the message, and the data contained within the message.
        """
        name, data = LOGGED.decode(name, data)
        timestamp = kwargs["timestamp"]
        source = kwargs["source"]
        self.event_log.append((timestamp, source, name, data))

    def _query(self, query_type, **kwargs):
        """Handles any query events received from pydra."""
        event_name = "query_" + query_type
        if event_name in self.events:
            self.events[event_name]()

    def query_messages(self):
        """Fulfills a request from pydra for messages."""
        while len(self.messages):
            source, t, m = self.messages.pop(0)
            serialized = EVENT_INFO.encode(t, source, m, dict())
            self.zmq_sender.send_multipart(serialized, zmq.SNDMORE)
        self.zmq_sender.send(b"")

    def query_events(self):
        """Fulfills a request from pydra for logged worker events."""
        for event in self.event_log:
            serialized = EVENT_INFO.encode(*event)
            self.zmq_sender.send_multipart(serialized, zmq.SNDMORE)
        self.zmq_sender.send(b"")
        self.event_log = []

    def query_data(self):
        """Fulfills a request from pydra for data."""
        for pipeline in self.savers:
            # name = pipeline.name
            pipeline_data = pipeline.flush()
            for source, data in pipeline_data.items():
                frame = data.pop("frame", np.empty([], dtype="uint8"))
                serialized = DATA_INFO.encode(source, data, frame)
                self.zmq_sender.send_multipart(serialized, zmq.SNDMORE)
        self.zmq_sender.send(b"")

    def recv_message(self, s, **kwargs):
        """Adds messages recevied from workers to the message log."""
        self.messages.append((kwargs["source"], kwargs["timestamp"], s))

    def recv_timestamped(self, t, data, **kwargs):
        self.targets[kwargs["source"]].update(kwargs["source"], "timestamped", t, data)

    def recv_indexed(self, t, i, data, **kwargs):
        self.targets[kwargs["source"]].update(kwargs["source"], "indexed", t, i, data)

    def recv_frame(self, t, i, frame, **kwargs):
        self.targets[kwargs["source"]].update(kwargs["source"], "frame", t, i, frame)

    def start_recording(self, directory: str = None, filename: str = None, **kwargs):
        """Implements a start_recording event. Starts saving data."""
        print("START RECORDING")
        for pipeline in self.savers:
            pipeline.start(directory, filename)
        self.recording = True

    def stop_recording(self, **kwargs):
        """Implements a stop_recording event. Stops saving data."""
        print("STOP RECORDING")
        if self.recording:
            for pipeline in self.savers:
                pipeline.stop()
            self.recording = False
