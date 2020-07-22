from ..core import AcquisitionWorker, FrameOutput
from multiprocessing import Queue
import time


class CameraAcquisition(AcquisitionWorker):

    def __init__(self, q: Queue, camera_type: type, camera_kwargs: dict = None, **kwargs):
        super().__init__(q, **kwargs)
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
        timestamp = time.clock()
        output = FrameOutput(self.frame_number, timestamp, frame)
        self.frame_number += 1
        return output

    def cleanup(self):
        self.camera.release()
