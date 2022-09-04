from pydra.classes import WorkerFactory
from ..pydra_module import PydraModule
from .camera import *
from .video import *
from .widget import *


class CameraModule(PydraModule):

    camera = Camera

    @classmethod
    def new(cls, name, *, subscriptions=(), saver=None, camera_args=(), camera_params=None):
        factory = WorkerFactory(name, CameraAcquisition, subscriptions)
        params = {"camera_type": cls.camera,
                  "camera_args": camera_args,
                  "camera_params": camera_params or {}}
        return cls(factory, params, saver, CameraWidget, FramePlotter)
