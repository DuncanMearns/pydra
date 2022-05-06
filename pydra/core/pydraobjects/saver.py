from .._base import *
from ..messaging import *
from ..utils import Parallelized
import numpy as np
import os
import cv2
from collections import deque


class SaverConstructor:
    """Container class for type, args, kwargs, and connections for Saver classes. Allows dynamically modified Saver
    types to be passed to new processes for instantiation.

    Parameters
    ----------
    cls_type : PydraType
        The class to be constructed. Should be a subclass of Saver.
    args : tuple
        A copy of the args class attribute.
    kwargs : dict
        A copy of the kwargs class attribute.
    connections : dict
        A copy of the  _connections private class attribute. Should be properly initialized with connections to backend.
    """

    def __init__(self, cls_type, args, kwargs, connections):
        self.cls_type = cls_type
        self.args = args
        self.kwargs = kwargs
        self.connections = connections

    def __call__(self, *args, **kwargs):
        """Returns a new Saver class that can be instantiated."""
        return type(self.cls_type.name, (self.cls_type,), {"args": self.args, "kwargs": self.kwargs,
                                                           "_connections": self.connections})


class Saver(Parallelized, PydraSender, PydraSubscriber):
    """Base saver class.

    Attributes
    ----------
    workers : tuple
        Tuple of worker names (str) that saver listens to.
    args : tuple
        Passed to *args when saver instantiated.
    kwargs : dict
        Passed to **kwargs when saver instantiated.
    _connections : dict
        Private attribute containing zmq connections. Must be set before instantiation.
    """

    workers = ()
    args = ()
    kwargs = {}
    _connections = {}

    # States
    idle = 0
    recording = 1

    @classmethod
    def start(cls, *args, **kwargs):
        """Overrides Parallelized start method. Spawns an instantiated Saver object in a new thread."""
        kw = cls.kwargs.copy()
        kw.update(cls._connections)
        return super().start_thread(*cls.args, **kw)

    @classmethod
    def to_constructor(cls):
        """Returns a constructor object for current saver class, preserving changes to class attributes."""
        return SaverConstructor(cls, cls.args, cls.kwargs, cls._connections)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = self.idle

    def setup(self):
        """Sends a connected signal."""
        self.connected()

    @_CONNECTION
    def connected(self):
        return True,

    @_CONNECTION
    def not_connected(self):
        return False,

    def _process(self):
        self.poll()

    def new_file(self, directory, filename, ext=""):
        if ext:
            filename = ".".join((filename, ext))
        f = os.path.join(directory, filename)
        return f


class VideoSaver(Saver):

    name = "video_saver"

    def __init__(self, frame_rate=100., fourcc="XVID", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame_rate = frame_rate
        self.fourcc = fourcc
        self.writer = None
        self.cached = np.empty(())
        self.t_cache = deque(np.empty(100) * np.nan, 100)

    @property
    def frame_size(self):
        return self.cached.shape[1], self.cached.shape[0]

    @property
    def is_color(self):
        return self.cached.ndim == 3

    @property
    def real_frame_rate(self):
        a = np.array(self.t_cache)
        a = a[~np.isnan(a)]
        return 1. / np.mean(np.diff(a))

    def recv_frame(self, t, i, frame, **kwargs):
        self.cached = frame
        self.t_cache.append(t)
        if i % 100 == 0:
            print(i, "received")
        if self.state == self.recording:
            self.writer.write(frame)

    def start_recording(self, directory=None, filename=None, **kwargs):
        path = self.new_file(directory, filename, "avi")
        print("video saver starts recording", path, self.real_frame_rate)
        self.state = self.recording
        fourcc = cv2.VideoWriter_fourcc(*self.fourcc)
        self.writer = cv2.VideoWriter(path, fourcc, self.frame_rate, self.frame_size, self.is_color)

    def stop_recording(self, **kwargs):
        self.writer.release()
        self.state = self.idle


class HDF5Saver(Saver):

    name = "hdf5_saver"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def recv_indexed(self, t, i, data, **kwargs):
        return

    def recv_array(self, t, i, a, **kwargs):
        return


class CSVSaver(Saver):

    name = "csv_saver"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def recv_timestamped(self, t, data, **kwargs):
        return
