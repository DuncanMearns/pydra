from pydra import Acquisition
import time
import numpy as np
from dataclasses import dataclass


__all__ = ("Camera", "CameraAcquisition", "setter")


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


@dataclass
class CameraParameters:
    # Controllable parameters
    frame_rate: float = None    # fps
    frame_width: int = None     # pixels
    frame_height: int = None    # pixels
    frame_x_offset: int = None  # pixels
    frame_y_offset: int = None  # pixels
    exposure: int = None        # microseconds
    gain: float = None          # gain value


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
        The current frame number of the camera.
    """

    camera_exception = Exception

    def __init__(
            self,
            frame_size: tuple = None,
            frame_rate: float = None,
            offsets: tuple = None,
            exposure: int = None,
            gain: float = None,
            *args, **kwargs):
        super().__init__(*args, **kwargs)
        # w, h = frame_size
        # x, y = offsets
        # self.params = CameraParameters(frame_rate, w, h, x, y, exposure, gain)
        # self.max_params = CameraParameters()
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
        """Implements the acquire method for a camera object.

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
        with self as cam:
            for param, val in params.items():
                setattr(cam, param, val)
                newval = getattr(cam, param)
                new_params[param] = newval
        self.params.update(new_params)
        return new_params

    # def _set_params(self, **params):
    #     new_params = {}
    #     for param, val in params.items():
    #         setattr(self, param, val)
    #         newval = getattr(self, param)
    #         new_params[param] = newval
    #         print(param, "set to", newval)
    #     self.params.update(new_params)
    #     return new_params

    def is_connected(self):
        return self.camera


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
        try:
            self.camera.setup()
        except Exception as e:
            self.catch_error(e, "Failed to connect to camera", critical=True)

    def acquire(self):
        """Implements the acquire method for a camera object.

        Retrieves a frame with the read method, computes the timestamp, publishes the frame data over 0MQ and then
        increments the frame number.
        """
        if not self.camera.is_connected():
            self.catch_error(self.camera.camera_exception(), "Failed to connect to camera", critical=True)
            return
        frame = self.camera.read()
        # Grab a frame
        # Get current time
        t = time.time()
        if isinstance(frame, np.ndarray) and frame.size:
            # Broadcast frame data through the network
            self.send_frame(self.frame_number, t, frame)
            # Increment the frame index
            self.frame_number += 1

    def cleanup(self):
        self.camera.shutdown()

    def set_params(self, params, **kwargs):
        if ("target" in kwargs) and (kwargs["target"] != self.name):
            return
        t = time.time()
        data = self.camera.__getattribute__("set_params")(*(), **params)  # call camera event
        self.send_timestamped(t, data)

    def check_params(self, **kwargs):
        if ("target" in kwargs) and (kwargs["target"] != self.name):
            return
        t = time.time()
        data = self.camera.params
        self.send_timestamped(t, data)

    def reset_frame_number(self, **kwargs):
        self.frame_number = 0
