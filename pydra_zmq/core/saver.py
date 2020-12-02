from .bases import ZMQSaver, ProcessMixIn
from .messaging import *
from .messaging.serializers import *
import threading
import queue
import zmq
import cv2
from pathlib import Path
from collections import deque


class Thread(threading.Thread):

    def __init__(self, path: str, q: queue.Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = str(path)
        self.q = q

    def setup(self):
        return

    def dump(self, *args):
        return

    def cleanup(self):
        return

    def run(self):
        self.setup()
        while True:
            try:
                data = self.q.get(timeout=0.01)
                if data:
                    self.dump(*data)
                else:
                    break
            except queue.Empty:
                pass
        self.cleanup()


class FrameThread(Thread):

    def __init__(self, path, q, frame_rate, frame_size, fourcc, is_color=False, *args, **kwargs):
        super().__init__(path, q, *args, **kwargs)
        self.frame_rate = frame_rate
        self.frame_size = frame_size
        self.fourcc = fourcc
        self.is_color = is_color
        self.writer = None

    def setup(self):
        fourcc = cv2.VideoWriter_fourcc(*self.fourcc)
        self.writer = cv2.VideoWriter(self.path, fourcc, self.frame_rate, self.frame_size, self.is_color)

    def dump(self, frame):
        frame = deserialize_array(frame)
        self.writer.write(frame)

    def cleanup(self):
        self.writer.release()


class IndexedThread(Thread):

    def __init__(self, path, q, *args, **kwargs):
        super().__init__(path, q, *args, **kwargs)
        self.data = None

    def setup(self):
        self.data = []

    def dump(self, t, i, data):
        t, i, data = DATA(INDEXED).decode(t, i, data)

    def cleanup(self):
        return


class TimestampedThread(Thread):

    def __init__(self, path, q, *args, **kwargs):
        super().__init__(path, q)

    def setup(self):
        self.data = []

    def dump(self, t, data):
        t, data = DATA(TIMESTAMPED).decode(t, data)

    def cleanup(self):
        return


class Group:

    def __init__(self, name, members):
        self.name = name
        self.members = members
        self.frame_q = queue.Queue()
        self.indexed_q = queue.Queue()
        self.timestamped_q = queue.Queue()
        # Frame handling
        self.last = None
        self.timestamps = deque(maxlen=1000)
        self.fourcc = "xvid"

    @property
    def frame_rate(self):
        return len(self.timestamps) / (self.timestamps[-1] - self.timestamps[0])

    @property
    def frame_size(self):
        return deserialize_array(self.last).shape[:2][::-1]

    @property
    def is_color(self):
        return deserialize_array(self.last).ndim > 2

    def update(self, t, i, frame):
        self.timestamps.append(deserialize_float(t))
        self.last = frame

    def frame(self, t, i, frame):
        self.frame_q.put((frame,))
        self.indexed_q.put((t, i, "null".encode("utf-8")))

    def indexed(self, t, i, data):
        self.indexed_q.put((t, i, data))

    def timestamped(self, t, data):
        self.timestamped_q.put((t, data))

    def start(self, directory, filename):
        # Base name
        filename = str(Path(directory).joinpath(filename + self.name))
        # Frame thread
        self.frame_thread = FrameThread(filename + ".avi", self.frame_q,
                                        self.frame_rate, self.frame_size, self.fourcc, self.is_color)
        self.frame_thread.start()
        # Indexed thread
        self.indexed_thread = IndexedThread(filename + ".csv", self.indexed_q)
        self.indexed_thread.start()
        # Timestamped thread
        self.timestamped_thread = TimestampedThread(filename + "_events.csv", self.timestamped_q)
        self.timestamped_thread.start()

    def stop(self):
        # Send termination signal
        self.timestamped_q.put(b"")
        self.indexed_q.put(b"")
        self.frame_q.put(b"")
        # Join threads
        self.timestamped_thread.join()
        self.indexed_thread.join()
        self.frame_thread.join()


class Saver(ZMQSaver, ProcessMixIn):

    name = "saver"

    def __init__(self, groups, video_params, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Message cache
        self.messages = []
        # Log
        self.log = []
        # Query events
        self.events["query_messages"] = self.query_messages
        self.events["query_data"] = self.query_data
        self.events["query_log"] = self.query_log
        # Recording
        self.events["start_recording"] = self.start_recording
        self.events["stop_recording"] = self.stop_recording
        self.recording = False
        # Groups
        self.groups = []
        self.targets = {}
        for name, members in groups.items():
            group = Group(name, members)
            self.groups.append(group)
            for members in members:
                self.targets[members] = group
        # Video params
        self.video_params = video_params
        # Data buffers
        self.timestamped = []
        self.indexed = []

    def _process(self):
        self._recv()

    def exit(self, *args, **kwargs):
        print(self.log)
        self.close()

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
        return

    def query_log(self):
        return

    def recv_message(self, s, **kwargs):
        self.messages.append((kwargs["source"], kwargs["timestamp"], s))

    def recv_log(self, timestamp, source, name, data):
        self.log.append((timestamp, source, name, data))

    def recv_timestamped(self, t, data, **kwargs):
        self.timestamped.append((t, data))
        if kwargs["save"] and self.recording:
            self.targets[kwargs["source"]].timestamped(t, data)
        return

    def recv_indexed(self, t, i, data, **kwargs):
        self.indexed.append((t, i, data))
        if kwargs["save"] and self.recording:
            self.targets[kwargs["source"]].indexed(t, i, data)
        return

    def recv_frame(self, t, i, frame, **kwargs):
        self.targets[kwargs["source"]].update(t, i, frame)
        if kwargs["save"] and self.recording:
            self.targets[kwargs["source"]].frame(t, i, frame)
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
