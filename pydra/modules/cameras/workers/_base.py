from pydra.core import Acquisition
from pydra.core.messaging import LOGGED
import time
import numpy as np


class CameraAcquisition(Acquisition):
    """Base class for cameras.

    Attributes
    ----------
    frame_size : tuple
        (Width, height) of the frame in pixels.
    frame_rate : float
        Target frame rate (fps)
    offsets : tuple
        The (x, y) offsets.
    exposure : int
        Exposure time of the frame (msec).
    gain : float
        Digital gain.
    camera : object
        Camera object from API.
    frame_number : int
        The current frame number of the acquisition.
    """

    def __init__(
            self,
            frame_size: tuple = None,
            frame_rate: float = None,
            offsets: tuple = None,
            exposure: int = None,
            gain: float = None,
            *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame_size = frame_size
        self.frame_rate = frame_rate
        self.offsets = offsets
        self.exposure = exposure
        self.gain = gain
        self.events["set_params"] = self.set_params
        self.events["start_recording"] = self.reset_frame_number
        self.camera = None
        self.frame_number = 0

    def acquire(self):
        """Implements the acquire method for an acquisition object.

        Retrieves a frame with the read method, computes the timestamp, publishes the frame data over 0MQ and then
        increments the frame number.
        """
        frame = self.read()
        t = time.time()
        self.send_frame(t, self.frame_number, frame)
        self.frame_number += 1

    def read(self) -> np.ndarray:
        """Read method for acquiring frames from the camera."""
        return self.empty()

    def set_frame_rate(self, fps: float) -> bool:
        self.frame_rate = fps
        return True

    def set_frame_size(self, width: int, height: int) -> bool:
        self.frame_size = (width, height)
        return True

    def set_offsets(self, x, y) -> bool:
        self.offsets = (x, y)
        return True

    def set_exposure(self, msec: int) -> bool:
        self.exposure = msec
        return True

    def set_gain(self, gain: float) -> bool:
        self.gain = gain
        return True

    @LOGGED
    def set_params(self, **kwargs):
        new_params = {}
        if ("target" in kwargs) and (kwargs["target"] != self.name):
            pass
        else:
            if "frame_rate" in kwargs:
                if self.set_frame_rate(kwargs["frame_rate"]):
                    new_params["frame_rate"] = kwargs["frame_rate"]
            if "frame_size" in kwargs:
                w, h = kwargs["frame_size"]
                if self.set_frame_size(w, h):
                    new_params["frame_size"] = (w, h)
            if "offsets" in kwargs:
                x, y = kwargs["offsets"]
                if self.set_offsets(x, y):
                    new_params["offsets"] = (x, y)
            if "exposure" in kwargs:
                if self.set_exposure(kwargs["exposure"]):
                    new_params["exposure"] = kwargs["exposure"]
            if "gain" in kwargs:
                if self.set_gain(kwargs["gain"]):
                    new_params["gain"] = kwargs["gain"]
        return new_params

    def reset_frame_number(self, **kwargs):
        self.frame_number = 0

    @staticmethod
    def empty():
        """Returns an empty frame"""
        return np.array([], dtype="uint8")
