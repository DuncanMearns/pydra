from ...base import VideoSaver
from ...configuration import PydraModule
from .camera import *
from .video import *
from .widget import *


class CameraModule(PydraModule):

    camera = Camera

    @classmethod
    def new(cls, name, *, subscriptions=(), saver=None, camera_args=(), camera_params=None):
        worker_cls = CameraAcquisition.copy(name, subscriptions)
        saver_cls = saver or VideoSaver.copy(name + "_saver")
        worker_kw = {"camera_type": cls.camera,
                     "camera_args": camera_args,
                     "camera_params": camera_params or {}}
        return cls(worker_cls, (), worker_kw, saver_cls, CameraWidget, FramePlotter)
