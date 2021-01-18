from ..core import Acquisition
import time
import numpy as np


class CameraAcquisition(Acquisition):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events["set_params"] = self.set_params
        self.events["start_recording"] = self.reset_frame_number
        self.camera = None
        self.frame_number = 0

    def acquire(self):
        frame = self.read()
        t = time.time()
        self.send_frame(t, self.frame_number, frame)
        self.frame_number += 1

    def read(self) -> np.ndarray:
        return np.array([], dtype="uint8")

    def set_params(self, **kwargs):
        return {}

    def reset_frame_number(self, **kwargs):
        self.frame_number = 0
