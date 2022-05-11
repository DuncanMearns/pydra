from collections import deque
import numpy as np


class DataCache:

    def __init__(self):
        self._arr = self.empty_array
        self._data = {}
        self._events = self.empty_cache

    @property
    def empty_cache(self):
        return []

    @property
    def empty_array(self):
        return []

    def append_data(self, t, i, data):
        for k, val in data:
            if k not in self._data:
                self._data[k] = self.empty_cache
            self._data[k].append((i, t, val))

    def append_array(self, t, i, arr):
        self._arr.append((i, t, arr))

    def append_event(self, t, data):
        self._events.append((t, data))

    def append(self, t, i: int = None, data: dict = None, arr: np.ndarray = None):
        if i is not None:
            # Append data
            if data:
                self.append_data(t, i, data)
            if arr:
                self.append_array(t, i, arr)
            return
        # Append event
        data = data or {}
        self.append_event(t, data)

    def clear(self):
        for param in self._data.keys():
            self._data[param] = self.empty_cache
        self._arr = self.empty_array
        self._events = self.empty_cache

    def __getitem__(self, item):
        try:
            return np.array(self._data[item], dtype=np.float)
        except KeyError:
            return np.empty((0, 3))


class TempCache(DataCache):

    def __init__(self, cachesize, arr_cachesize=None):
        self.cachesize = cachesize
        self.arr_cachesize = arr_cachesize or cachesize
        super().__init__()

    @property
    def empty_cache(self):
        return deque(maxlen=self.cachesize)

    @property
    def empty_array(self):
        return deque(maxlen=self.arr_cachesize)

    def clear(self):
        for param, cache in self._data.items():
            cache.clear()
        self._arr.clear()
        self._events.clear()

    def set_cachesize(self, size):
        self.cachesize = size
        for param in self._data.keys():
            self._data[param] = deque(maxlen=self.cachesize)
        self._events = deque(maxlen=self.cachesize)

    def set_arr_cachesize(self, size):
        self._arr = deque(maxlen=size)
