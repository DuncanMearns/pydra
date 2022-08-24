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
import pandas as pd


recording_state = state_descriptor.new_type("recording_state")


class SaverConstructor:
    """Container class for type, args, kwargs, and connections for Saver classes. Allows dynamically modified Saver
    types to be passed to new processes for instantiation.

    Parameters
    ----------
    cls_type : PydraType
        The class to be constructed. Should be a subclass of Saver.
    workers : tuple
        A copy of the workers class attribute
    args : tuple
        A copy of the args class attribute.
    kwargs : dict
        A copy of the kwargs class attribute.
    connections : dict
        A copy of the  _connections private class attribute. Should be properly initialized with connections to backend.
    """

    def __init__(self, cls_type, workers, args, kwargs, connections):
        self.cls_type = cls_type
        self.workers = workers
        self.args = args
        self.kwargs = kwargs
        self.connections = connections

    def __call__(self, *args, **kwargs):
        """Returns a new Saver class that can be instantiated."""
        return type(self.cls_type.name, (self.cls_type,), {"workers": self.workers,
                                                           "args": self.args,
                                                           "kwargs": self.kwargs,
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
        return SaverConstructor(cls, cls.workers, cls.args, cls.kwargs, cls._connections)

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


class CachedSaver(Saver):

    name = "cached_saver"

    def __init__(self, cache=50000, arr_cache=500, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cachesize = cache
        self.arr_cachesize = arr_cache
        self.caches = dict([(worker, DataCache()) for worker in self.workers])
        self.temp = dict([(worker, TempCache(self.cachesize, self.arr_cachesize)) for worker in self.workers])

    def recv_indexed(self, t, i, data, **kwargs):
        self.recv_data(t, i, data, **kwargs)

    def recv_array(self, t, i, a, **kwargs):
        self.recv_data(t, i, arr=a, **kwargs)

    def recv_timestamped(self, t, data, **kwargs):
        self.recv_data(t, data=data, **kwargs)

    def recv_data(self, t, i=None, data=None, arr=None, **kwargs):
        worker = kwargs["source"]
        self.temp[worker].append(t, i, data, arr)
        if self.recording:
            self.save_data(worker, t, i, data, arr)

    def save_data(self, worker, t, i, data, arr):
        self.caches[worker].append(t, i, data, arr)

    def stop_recording(self, **kwargs):
        for cache in self.caches.values():
            cache.clear()
        super().stop_recording(**kwargs)

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


class CSVSaver(CachedSaver):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = "no_file.csv"

    def start_recording(self, directory=None, filename=None, idx=0, **kwargs):
        super().start_recording(directory=directory, filename=filename, idx=idx, **kwargs)
        self.path = self.new_file(directory, filename, "csv")

    def stop_recording(self, **kwargs):
        i = 0
        all_t = []
        all_params = ["time"]
        all_data = {}
        for worker, cache in self.caches.items():
            for t, data in cache.events:
                all_t.append(t)
                for param, val in data.items():
                    param_name = ".".join([worker, param])
                    if param_name not in all_params:
                        all_params.append(param_name)
                    if param_name in all_data:
                        all_data[param_name].append((i, val))
                    else:
                        all_data[param_name] = [(i, val)]
                i += 1
        dfs = []
        if all_data:
            for param, data in all_data.items():
                idxs, vals = zip(*data)
                df = pd.DataFrame(data=vals, index=idxs, columns=[param])
                dfs.append(df)
            df = pd.concat(dfs, axis=1, ignore_index=False, verify_integrity=False)
            df["time"] = all_t
            df = df[all_params]
            df.to_csv(self.path, index=False)
        super().stop_recording(**kwargs)


class HDF5Saver(CachedSaver):

    name = "hdf5_saver"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.h5_file = None

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
        for worker in self.workers:
            self.h5_file.create_group(worker)

    def stop_recording(self, **kwargs):
        for worker, cache in self.caches.items():
            group = self.h5_file[worker]
            for name, data in cache.data.items():
                group.create_dataset(name, data=data)
        self.h5_file.close()
        for cache in self.caches.values():
            cache.clear()
        super().stop_recording(**kwargs)


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
        if self.recording:
            self.save_frame(t, i, frame)

    def recv_timestamped(self, t, data, **kwargs):
        self.frame_rate = data.get("frame_rate", self.frame_rate)
        super().recv_timestamped(t, data, **kwargs)

    def save_frame(self, t, i, frame):
        self.writer.write(frame)
        self.t_cache.append((i, t))

    def start_recording(self, directory=None, filename=None, idx=0, **kwargs):
        super().start_recording(directory, filename, idx, **kwargs)
        path = self.new_file(directory, filename, "avi")
        print("video saver starts recording", path, self.frame_rate, self.real_frame_rate)
        fourcc = cv2.VideoWriter_fourcc(*self.fourcc)
        self.writer = cv2.VideoWriter(path, fourcc, self.frame_rate, self.frame_size, self.is_color)

    def stop_recording(self, **kwargs):
        self.writer.release()
        try:
            group = self.h5_file[self.source]
            dset = "video_metadata"
        except KeyError:
            group = self.h5_file
            dset = self.source
        group.create_dataset(dset, data=np.array(self.t_cache))
        self.t_cache = []
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
