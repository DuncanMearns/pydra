from .._base import PydraSubscriber
from ..utils.cache import TempCache


class GUIBackend(PydraSubscriber):

    name = "backend"
    subscriptions = ()

    def __init__(self, cache=50000, arr_cache=500, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cachesize = cache
        self.arr_cachesize = arr_cache
        self.caches = dict([(worker, TempCache(self.cachesize, self.arr_cachesize)) for worker in self.subscriptions])
        self.frames = {}

    def raise_error(self, error: Exception, message: str):
        raise(error)

    def recv_indexed(self, t, i, data, **kwargs):
        self.recv_data(t, i, data, **kwargs)

    def recv_array(self, t, i, a, **kwargs):
        self.recv_data(t, i, arr=a, **kwargs)

    def recv_timestamped(self, t, data, **kwargs):
        self.recv_data(t, data=data, **kwargs)

    def recv_frame(self, t, i, frame, **kwargs):
        worker = kwargs["source"]
        self.frames[worker] = frame

    def recv_data(self, t, i=None, data=None, arr=None, **kwargs):
        worker = kwargs["source"]
        self.caches[worker].append(t, i, data, arr)

    def flush(self) -> dict:
        flushed = {}
        for worker, cache in self.caches.items():
            flushed[worker] = {
                "data": cache.data,
                "array": cache.arr,
                "events": cache.events
            }
            cache.clear()
            if worker in self.frames:
                frame = self.frames.pop(worker)
                flushed[worker]["frame"] = frame
        return flushed
