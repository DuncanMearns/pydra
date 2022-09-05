from .worker import Saver
from ..utils.cache import DataCache

import numpy as np
import cv2
from collections import deque
import h5py
import pandas as pd


__all__ = ("CachedSaver", "CSVSaver", "HDF5Saver", "VideoSaver")


class CachedSaver(Saver):

    name = "cached_saver"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.caches = dict([(worker, DataCache()) for worker in self.subscriptions])

    def recv_indexed(self, t, i, data, **kwargs):
        self.recv_data(t, i, data, **kwargs)

    def recv_array(self, t, i, a, **kwargs):
        self.recv_data(t, i, arr=a, **kwargs)

    def recv_timestamped(self, t, data, **kwargs):
        self.recv_data(t, data=data, **kwargs)

    def recv_data(self, t, i=None, data=None, arr=None, **kwargs):
        worker = kwargs["source"]
        # self.temp[worker].append(t, i, data, arr)
        if self.recording:
            self.save_data(worker, t, i, data, arr)

    def save_data(self, worker, t, i, data, arr):
        self.caches[worker].append(t, i, data, arr)

    def stop_recording(self, **kwargs):
        for cache in self.caches.values():
            cache.clear()
        super().stop_recording(**kwargs)


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
        for worker in self.subscriptions:
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

    def __init__(self, frame_rate=100., fourcc="XVID", cachesize=500, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.source = self.name
        self.frame_rate = frame_rate
        self.fourcc = fourcc
        self.writer = None
        self.video_cache = np.empty(())
        self.t_cache = []
        self.t_temp = deque(np.empty(cachesize) * np.nan, cachesize)

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
