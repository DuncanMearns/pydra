from .._base import *
from ..messaging import *
from ..utils.cache import DataCache, TempCache
from ..utils.state import state_descriptor
from ._runner import Parallelized

import numpy as np
import os
import cv2
from collections import deque
import h5py


recording_state = state_descriptor.new_type("recording_state")


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
    idle = recording_state(0)
    recording = recording_state(1)

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
        self.idle()

    def setup(self):
        """Sends a connected signal."""
        self.connected()

    @BACKEND.CONNECTION
    def connected(self):
        return True,

    @BACKEND.CONNECTION
    def not_connected(self):
        return False,

    def _process(self):
        self.poll()

    @staticmethod
    def new_file(directory, filename, ext=""):
        if ext:
            filename = ".".join((filename, ext))
        f = os.path.join(directory, filename)
        return f

    def flush(self) -> dict:
        return {}

    @BACKEND.DATA
    def reply_data(self):
        flushed = self.flush()
        return flushed,

    def start_recording(self, directory=None, filename=None, idx=0, **kwargs):
        self.recording()

    def stop_recording(self, **kwargs):
        self.idle()


class HDF5Saver(Saver):

    name = "hdf5_saver"

    def __init__(self, cache=50000, arr_cache=500, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.h5_file = None
        self.cachesize = cache
        self.arr_cachesize = arr_cache
        self.caches = dict([(worker, DataCache()) for worker in self.workers])
        self.temp = dict([(worker, TempCache(self.cachesize, self.arr_cachesize)) for worker in self.workers])

    @property
    def h5_file(self) -> h5py.File:
        if self._h5_file:
            return self._h5_file

    @h5_file.setter
    def h5_file(self, val):
        self._h5_file = val

    def start_recording(self, directory=None, filename=None, idx=0, **kwargs):
        super().start_recording(directory=directory, filename=filename, idx=idx, **kwargs)
        path = self.new_file(directory, filename, "hdf5")
        self.h5_file = h5py.File(path, "w")

    def stop_recording(self, **kwargs):
        # stuff here
        super().stop_recording(**kwargs)

    def recv_indexed(self, t, i, data, **kwargs):
        self.recv_data(t, i, data)

    def recv_array(self, t, i, a, **kwargs):
        self.recv_data(t, i, arr=a)

    def recv_timestamped(self, t, data, **kwargs):
        self.recv_data(t, data=data)

    def recv_data(self, t, i=None, data=None, arr=None, **kwargs):
        worker = kwargs["source"]
        self.temp[worker].append(t, i, data, arr)
        if self.recording:
            self.save_data(worker, t, i, data, arr)

    def save_data(self, worker, t, i, data, arr):
        self.caches[worker].append(t, i, data, arr)

    def flush(self) -> dict:
        flushed = super().flush()
        data = {}
        for worker, cache in self.temp.items():
            if worker in flushed.keys():
                raise ValueError("Saver is overwriting data in cache when flushed.")
            data[worker] = {
                "data": cache.data,
                "array": cache.arr,
                "events": cache.events
            }
            cache.clear()
        flushed.update(data)
        return flushed


class VideoSaver(HDF5Saver):

    name = "video_saver"

    def __init__(self, frame_rate=100., fourcc="XVID", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.source = self.name
        self.frame_rate = frame_rate
        self.fourcc = fourcc
        self.writer = None
        self.video_cache = np.empty(())
        self.t_cache = []
        self.t_temp = deque(np.empty(self.arr_cachesize) * np.nan, self.arr_cachesize)

    @property
    def frame_size(self):
        return self.video_cache.shape[1], self.video_cache.shape[0]

    @property
    def is_color(self):
        return self.video_cache.ndim == 3

    @property
    def real_frame_rate(self):
        a = np.array(self.t_temp)
        a = a[~np.isnan(a)]
        if len(a) > 1:
            return 1. / np.mean(np.diff(a))
        return 0

    def recv_frame(self, t, i, frame, **kwargs):
        self.source = kwargs["source"]
        self.video_cache = frame
        self.t_temp.append(t)
        if i % 100 == 0:
            print(i, "received")
        if self.recording:
            self.save_frame(t, i, frame)

    def save_frame(self, t, i, frame):
        self.writer.write(frame)
        self.t_cache.append((t, i))

    def start_recording(self, directory=None, filename=None, idx=0, **kwargs):
        super().start_recording(directory, filename, idx, **kwargs)
        path = self.new_file(directory, filename, "avi")
        print("video saver starts recording", path, self.real_frame_rate)
        fourcc = cv2.VideoWriter_fourcc(*self.fourcc)
        self.writer = cv2.VideoWriter(path, fourcc, self.frame_rate, self.frame_size, self.is_color)
        self.t_cache = []

    def stop_recording(self, **kwargs):
        self.writer.release()
        self.h5_file.create_dataset(self.name, data=np.array(self.t_cache))
        super().stop_recording(**kwargs)

    def flush(self) -> dict:
        flushed = super().flush()
        data = {
            "frame": self.video_cache,
            "frame_rate": self.real_frame_rate
        }
        if self.source in flushed.keys():
            flushed[self.source].update(data)
        else:
            flushed[self.source] = data
        return flushed
