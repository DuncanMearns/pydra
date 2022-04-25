from .._base import *
from ..messaging import *
from ..utils import Parallelized
import numpy as np


class Saver(Parallelized, PydraSender, PydraSubscriber):

    workers = ()
    args = ()
    kwargs = {}
    _connections = {}

    @classmethod
    def start(cls, *args, **kwargs):
        kw = cls.kwargs.copy()
        kw.update(cls._connections)
        return super().start_thread(*cls.args, **kw)

    @classmethod
    def to_tuple(cls):
        return cls, cls.args, cls.kwargs, cls._connections

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setup(self):
        self.connected()

    @_CONNECTION
    def connected(self):
        return True,

    @_CONNECTION
    def not_connected(self):
        return False,

    def _process(self):
        self.poll()


class VideoSaver(Saver):

    name = "video_saver"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame_rate = None
        self.fourcc = None
        self.writer = None
        self.cached = np.empty(())

    @property
    def frame_size(self):
        return self.cached.shape[1], self.cached.shape[0]

    @property
    def is_color(self):
        return self.cached.ndim == 3

    def recv_frame(self, t, i, frame, **kwargs):
        self.cached = frame
        return


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
