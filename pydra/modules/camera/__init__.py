from ...base import VideoSaver
from ...configuration import PydraModule
from .camera import *
from .video import *
from .widget import *
import os


class BehaviorSaver(VideoSaver):

    name = "eye_camera_saver"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_callbacks["run"] = self.dummy

    @staticmethod
    def new_file(directory, filename, ext=""):
        if ext:
            filename = ".".join((filename + "_eye", ext))
        f = os.path.join(directory, filename)
        return f

    def dummy(self, *args, **kwargs):
        """ This needs to be here to prevent pydra event messages calling the run method accidentally because Duncan sucks at programming :( """
        return


class CameraModule(PydraModule):

    camera = Camera

    @classmethod
    def new(cls, name, *, subscriptions=(), saver=BehaviorSaver, camera_args=(), camera_params=None):
        worker_cls = CameraAcquisition.copy(name, subscriptions)
        saver_cls = saver or VideoSaver.copy(name + "_saver")
        worker_kw = {"camera_type": cls.camera,
                     "camera_args": camera_args,
                     "camera_params": camera_params or {}}
        return cls(worker_cls, (), worker_kw, saver_cls, CameraWidget, FramePlotter)
