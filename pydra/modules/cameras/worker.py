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

    def set_exposure(self, u: int) -> bool:
        self.exposure = u
        return True

    def set_gain(self, gain: float) -> bool:
        self.gain = gain
        return True

    @LOGGED
    def set_params(self, **kwargs):
        # print("SETTING PARAMS")
        new_params = {}
        if ("target" in kwargs) and (kwargs["target"] != self.name):
            pass
        else:
            for param in ("frame_rate", "frame_size", "offsets", "exposure", "gain"):
                if param in kwargs:
                    val = kwargs[param]
                    setter = getattr(self, "_".join(["set", param]))
                    try:
                        ret = setter(*val)
                    except TypeError:
                        ret = setter(val)
                    if ret:
                        new_params["param"] = val
                    else:
                        print(f"Param {param} could not be set to {val}")
        return new_params

    def reset_frame_number(self, **kwargs):
        self.frame_number = 0

    @staticmethod
    def empty():
        """Returns an empty frame"""
        return np.array([], dtype="uint8")
