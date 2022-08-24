from pydra import Acquisition
import time
import numpy as np
from .widget import CameraWidget, FramePlotter


__all__ = ("Camera", "CameraAcquisition", "CAMERA", "setter")


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


class Camera:
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
        self.camera = None
        self.frame_number = 0

    def setup(self):
        return

    def shutdown(self):
        return

    def read(self) -> np.ndarray:
        """Implements the acquire method for an acquisition object.

        Retrieves a frame with the read method, computes the timestamp, publishes the frame data over 0MQ and then
        increments the frame number.
        """
        return self.empty()

    @staticmethod
    def empty():
        """Returns an empty frame"""
        return np.array([], dtype="uint8")

    def set_params(self, **params):
        new_params = {}
        for param, val in params.items():
            setattr(self, param, val)
            newval = getattr(self, param)
            new_params[param] = newval
            print(param, "set to", newval)
        self.params.update(new_params)
        return new_params


class CameraAcquisition(Acquisition):
    """Acquisition class for cameras."""

    def __init__(self, camera_type, camera_args=None, camera_params=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.camera_type = camera_type
        self.camera_args = camera_args or ()
        self.camera_params = camera_params or {}
        self.camera = None
        self.event_callbacks["start_recording"] = self.reset_frame_number
        self.frame_number = 0

    def setup(self):
        self.camera = self.camera_type(*self.camera_args, **self.camera_params)  # instantiate camera object
        self.camera.setup()
        self.send_timestamped(time.time(), self.camera.params)

    def acquire(self):
        """Implements the acquire method for an acquisition object.

        Retrieves a frame with the read method, computes the timestamp, publishes the frame data over 0MQ and then
        increments the frame number.
        """
        # Grab a frame
        frame = self.camera.read()
        # Get current time
        t = time.time()
        if isinstance(frame, np.ndarray) and frame.size:
            # Broadcast frame data through the network
            self.send_frame(t, self.frame_number, frame)
            # Increment the frame index
            self.frame_number += 1

    def cleanup(self):
        self.camera.shutdown()

    def set_params(self, params, **kwargs):
        t = time.time()
        if ("target" in kwargs) and (kwargs["target"] != self.name):
            pass
        else:
            data = self.camera.__getattribute__("set_params")(*(), **params)  # call camera event
            self.send_timestamped(t, data)

    def reset_frame_number(self, **kwargs):
        self.frame_number = 0


CAMERA = {
    "worker": CameraAcquisition,
    "params": {},
    "controller": CameraWidget,
    "plotter": FramePlotter
}
