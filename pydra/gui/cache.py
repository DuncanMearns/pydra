from collections import deque
import numpy as np


class WorkerCache:

    def __init__(self, cachesize=50000, **kwargs):
        self.cachesize = cachesize
        self.array = np.empty([])
        self._caches = {}
        self._events = []
        self._index_cache = deque(maxlen=self.cachesize)
        self._time_cache = deque(maxlen=self.cachesize)

    def update(self, t0, data, frame):
        t = np.array(data.get("time", [])) - t0
        i = np.array(data.get("index", []))
        self._time_cache.extend(t)
        self._index_cache.extend(i)
        for param, vals in data.get("data", {}).items():
            try:
                self._caches[param].extend(vals)
            except KeyError:
                self._caches[param] = deque(maxlen=self.cachesize)
                self._caches[param].extend(vals)
        self._events.extend(data.get("timestamped", []))
        if len(frame.shape):
            self.array = frame

    def clear(self):
        self._index_cache.clear()
        self._time_cache.clear()
        for param, cache in self._caches.items():
            cache.clear()
        self._events = []

    def set_cachesize(self, size):
        self.cachesize = size
        self._index_cache = deque(maxlen=self.cachesize)
        self._time_cache = deque(maxlen=self.cachesize)
        for param in self._caches.keys():
            self._caches[param] = deque(maxlen=self.cachesize)

    @property
    def index(self):
        return np.array(self._index_cache)

    @property
    def time(self):
        return np.array(self._time_cache)

    @property
    def events(self):
        return self._events

    def __getitem__(self, item):
        try:
            return np.array(self._caches[item], dtype=np.float)
        except KeyError:
            return []

    i = index
    t = time
