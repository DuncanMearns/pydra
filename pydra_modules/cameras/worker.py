from pydra.core import Acquisition
from pydra.messaging import LOGGED
import time
import numpy as np


class setter:

    def __init__(self, fset=None):
        self.fset = fset

    def __set_name__(self, owner, name):
        self.public_name = name
        self.private_name = "_" + name

    def __set__(self, instance, value):
        if self.fset is None:
            raise AttributeError(f"{self.public_name} not implemented")
        newval = self.fset(instance, value)
        setattr(instance, self.private_name, newval)

    def __get__(self, instance, owner):
        return getattr(instance, self.private_name)


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
        self.params = dict(
            frame_size=frame_size,
            frame_rate = frame_rate,
            offsets=offsets,
            exposure=exposure,
            gain=gain
        )
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

    @LOGGED
    def set_params(self, params, **kwargs):
        new_params = {}
        if ("target" in kwargs) and (kwargs["target"] != self.name):
            pass
        else:
            for param, val in params.items():
                setattr(self, param, val)
                newval = getattr(self, param)
                new_params[param] = newval
                print(param, "set to", newval)
        self.params.update(new_params)
        return new_params

    def reset_frame_number(self, **kwargs):
        self.frame_number = 0

    @staticmethod
    def empty():
        """Returns an empty frame"""
        return np.array([], dtype="uint8")
