from pydra.core.base import PydraSender, PydraSubscriber
from pydra.core.process import ProcessMixIn
from pydra.core.messaging import *
from .threading import *
import zmq
import queue
from pathlib import Path
from collections import deque
import numpy as np


class PydraSaver(ProcessMixIn, PydraSender, PydraSubscriber):
    """Singleton Saver class that integrates and handles incoming messages from all workers.

    Parameters
    ----------
    pipelines : dict
        Dictionary of workers (as a list of names) assigned to each pipeline (keys). Passed from pydra pipelines
        property.

    Attributes
    ----------
    event_log : list
        Logged messages from pydra objects.
    messages : list
        List of string-type messages received from pydra objects.
    recording : bool
        Stores whether data are currently being saved.
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
            saver = Saver(name, members)
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
        """Fulfills a request from pydra for logged events."""
        for event in self.event_log:
            serialized = EVENT_INFO.encode(*event)
            self.zmq_sender.send_multipart(serialized, zmq.SNDMORE)
        self.zmq_sender.send(b"")
        self.event_log = []

    def query_data(self):
        """Fulfills a request from pydra for data."""
        for pipeline in self.savers:  # iterate through pipeline objects in the savers attribute
            pipeline_data = pipeline.flush()  # flush cached data from the pipeline
            for source, data in pipeline_data.items():  # iterate through data from the cache
                a = data.pop("array", np.empty([]))  # remove array data
                serialized = DATA_INFO.encode(source, data, a)  # serialize the data for sending over ZeroMQ
                self.zmq_sender.send_multipart(serialized, zmq.SNDMORE)  # send to pydra
        self.zmq_sender.send(b"")  # send empty byte to let pydra know query has been fulfilled

    def recv_message(self, s, **kwargs):
        """Adds messages recevied from workers to the message log."""
        self.messages.append((kwargs["source"], kwargs["timestamp"], s))

    def recv_timestamped(self, t, data, **kwargs):
        """Sends timestamped data messages to the appropriate saver."""
        self.targets[kwargs["source"]].update(kwargs["source"], "timestamped", t, data)

    def recv_indexed(self, t, i, data, **kwargs):
        """Sends indexed data messages to the appropriate saver."""
        self.targets[kwargs["source"]].update(kwargs["source"], "indexed", t, i, data)

    def recv_array(self, t, i, a, **kwargs):
        """Sends indexed array messages to the appropriate saver."""
        self.targets[kwargs["source"]].update(kwargs["source"], "array", t, i, a)

    def recv_frame(self, t, i, frame, **kwargs):
        """Sends frame data messages to the appropriate saver."""
        self.targets[kwargs["source"]].update(kwargs["source"], "frame", t, i, frame)

    def start_recording(self, directory: str = None, filename: str = None, **kwargs):
        """Implements a start_recording event. Starts saving data."""
        print("START RECORDING")
        if not self.recording:
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


def saver(method):
    """Decorator that sends data to the appropriate saving method when recording."""
    def wrapper(obj, source, dtype, *args):
        if obj.recording:
            obj.save_methods[dtype](source, *args)
        method(obj, source, dtype, *args)
    return wrapper


class Saver:

    def __init__(self, name: str, members: list):
        self.name = name
        self.members = members
        # Queues
        self.frame_q = queue.Queue()
        self.indexed_q = queue.Queue()
        self.timestamped_q = queue.Queue()
        # Save methods
        self.recording = False
        self.save_methods = {
            "frame": self.save_frame,
            "indexed": self.save_indexed,
            "array": self.save_array,
            "timestamped": self.save_timestamped
        }
        # Data handling
        self.frame = None
        self.timestamps = deque(maxlen=1000)
        self.data_cache = {}
        self.fourcc = "XVID"

    @property
    def frame_rate(self) -> float:
        """Returns the actual frame rate of data acquisition."""
        return len(self.timestamps) / (self.timestamps[-1] - self.timestamps[0])

    @property
    def frame_size(self) -> tuple:
        """Returns the (width, height) of the last frame received."""
        return self.frame.shape[:2][::-1]

    @property
    def is_color(self) -> bool:
        """Returns whether incoming frames are color."""
        return self.frame.ndim > 2

    @saver
    def update(self, source, dtype, *args):
        """Called by pydra saver object when new data are received from workers."""
        # create cache for storing all data from a given source
        if source not in self.data_cache:
            self.data_cache[source] = {
                "time": [],
                "index": [],
                "data": {},
                "timestamped": [],
                "array": np.empty([])
            }
        # parse arguments
        data = {}
        if dtype == "frame":
            t, i, frame = args
            self.timestamps.append(t)
            self.frame = frame
            self.data_cache[source]["array"] = frame
        elif dtype == "indexed":
            t, i, data = args
        elif dtype == "array":
            t, i, a = args
            self.data_cache[source]["array"] = a
            return
        elif dtype == "timestamped":
            t, data = args
            self.data_cache[source]["timestamped"] = [(t, data)]
            return
        else:
            return
        # update indexed data in cache
        if t not in self.data_cache[source]["time"]:
            self.data_cache[source]["time"].append(t)
        if i not in self.data_cache[source]["index"]:
            self.data_cache[source]["index"].append(i)
        for key, val in data.items():
            try:
                self.data_cache[source]["data"][key].append(val)
            except KeyError:
                self.data_cache[source]["data"][key] = [val]

    def flush(self) -> dict:
        """Returns and clears all cached data."""
        data_cache = self.data_cache.copy()
        self.data_cache = {}
        return data_cache

    def save_frame(self, source, t, i, frame):
        """Parses frame data into appropriate queues for saving."""
        self.frame_q.put((source, frame))
        self.indexed_q.put((source, t, i, {}))

    def save_indexed(self, source, t, i, data):
        """Puts indexed data into appropriate queue for saving."""
        self.indexed_q.put((source, t, i, data))

    def save_array(self, source, t, i, a):
        """Puts array data into appropriate queue for saving."""
        self.indexed_q.put((source, t, i, {}, a))

    def save_timestamped(self, source, t, data):
        """Puts timestamped data into appropriate queue for saving."""
        self.timestamped_q.put((source, t, data))

    def start(self, directory, filename):
        """Starts threads for saving incoming data."""
        # Create filepath from directory and pipeline
        directory = Path(directory)
        if not directory.exists():
            directory.mkdir(parents=True)
        if self.name:
            filename = "_".join([filename, self.name])
        filepath = str(directory.joinpath(filename))
        # Frame thread
        if self.frame is not None:
            self.frame_thread = FrameThread(filepath + ".avi", self.frame_q, int(self.frame_rate), self.frame_size,
                                            self.fourcc, self.is_color)
            self.frame_thread.start()
        else:
            self.frame_thread = None
        # Indexed thread
        self.indexed_thread = IndexedThread(filepath + ".csv", self.indexed_q)
        self.indexed_thread.start()
        # Timestamped thread
        self.timestamped_thread = TimestampedThread(filepath + "_events.csv", self.timestamped_q)
        self.timestamped_thread.start()
        # Set recording to True
        self.recording = True

    def stop(self):
        """Terminates and joins saving threads."""
        # Send termination signal
        self.timestamped_q.put(b"")
        self.indexed_q.put(b"")
        self.frame_q.put(b"")
        # Join threads
        self.timestamped_thread.join()
        self.indexed_thread.join()
        if self.frame_thread:
            self.frame_thread.join()
        # Set recording to False
        self.recording = False
