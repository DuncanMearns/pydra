from collections import deque
import numpy as np


def decorator():
    def decorates(method):
        return method
    return decorates



class state_descriptor:

    def __init__(self, val, instance=None):
        self.val = val
        self.instance = instance

    def __get__(self, instance, owner):
        return type(self)(self.val, instance)

    def __call__(self):
        setattr(self.instance, self.name, self.val)

    def __bool__(self):
        return getattr(self.instance, self.name) == self.val

    def __repr__(self):
        binding = "bound" if self.instance else "unbound"
        return f"<{binding} {self.name} object with value {self.val}>"

    @property
    def name(self):
        return type(self).__name__

    @classmethod
    def new_type(cls, name):
        return type(name, (cls,), {})


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
        for k, val in data.items():
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
            if arr is not None:
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

    @property
    def data(self) -> dict:
        return dict(self._data)

    @property
    def arr(self) -> np.ndarray:
        return np.array(self._arr)

    @property
    def events(self) -> list:
        return list(self._events)


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

    @property
    def data(self) -> dict:
        return dict([(k, list(vals)) for k, vals in self._data.items()])
