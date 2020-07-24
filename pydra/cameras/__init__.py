from ..core import Plugin, AcquisitionWorker, FrameOutput
from .cameras import PikeCamera as PikeCameraType
from multiprocessing import Queue
import time


class CameraAcquisitionWorker(AcquisitionWorker):

    def __init__(self, q: Queue, camera_type: type, camera_kwargs: dict = None, *args, **kwargs):
        super().__init__(q, *args, **kwargs)
        self.camera_type = camera_type
        self.camera_kwargs = {}
        if camera_kwargs is not None:
            self.camera_kwargs.update(camera_kwargs)
        self.camera = None
        self.frame_number = 0

    def setup(self):
        self.camera = self.camera_type(**self.camera_kwargs)
        self.camera.open_camera()
        self.frame_number = 0

    def acquire(self):
        frame = self.camera.read()
        timestamp = time.time()
        output = FrameOutput(self.frame_number, timestamp, frame)
        self.frame_number += 1
        return output

    def cleanup(self):
        self.camera.release()


class PikeCamera(Plugin):

    name = 'PikeCamera'
    worker = CameraAcquisitionWorker
    widget = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params['camera_type'] = PikeCameraType
