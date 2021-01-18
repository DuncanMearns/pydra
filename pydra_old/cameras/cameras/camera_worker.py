from pydra.core import AcquisitionWorker, FrameOutput
from multiprocessing import Queue
import time


class CameraAcquisitionWorker(AcquisitionWorker):

    def __init__(self, q: Queue, frame_size, frame_rate, exposure, gain, *args, **kwargs):
        super().__init__(q, *args, **kwargs)
        self.width, self.height = frame_size
        self.frame_rate = frame_rate
        self.exposure = exposure
        self.gain = gain
        self.camera = None
        self.frame_number = 0

    def open(self):
        return

    def read(self):
        return

    def release(self):
        return

    def setup(self):
        self.open()
        self.frame_number = 0

    def acquire(self):
        frame = self.read()
        timestamp = time.time()
        output = FrameOutput(self.frame_number, timestamp, frame)
        self.frame_number += 1
        return output

    def cleanup(self):
        self.release()
