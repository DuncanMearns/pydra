from pydra import Acquisition, EVENT
import time
import numpy as np
from threading import Thread
import queue
from .widget import CameraWidget, FramePlotter


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


def camera_thread(camera_type, receive_q, send_q, camera_args, camera_params):
    camera = camera_type(*camera_args, **camera_params)  # instantiate camera object
    camera.setup()  # run any necessary setup code
    send_q.put_nowait(camera.params)  # send current camera params to worker
    while True:  # event loop
        try:
            (tag, name, args, kwargs) = receive_q.get(block=True, timeout=0.001)  # get messages from worker
            if tag == "exit":  # shutdown camera and return from thread if exit signal received
                camera.shutdown()
                return
            if tag == "event":  # handle events from worker
                try:
                    ret = camera.__getattribute__(name)(*args, **kwargs)  # call camera event
                    send_q.put_nowait(ret)  # send output back to worker
                except AttributeError:
                    continue
        except queue.Empty:  # if no messages from worker
            pass
        frame = camera.read()
        send_q.put_nowait(frame)


class CameraAcquisition(Acquisition):
    """Acquisition class for cameras."""

    def __init__(self, camera_type, camera_args=None, camera_params=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.camera_type = camera_type
        self.camera_args = camera_args or ()
        self.camera_params = camera_params or {}
        self.event_callbacks["start_recording"] = self.reset_frame_number
        self.frame_number = 0

    def setup(self):
        self.q_to_thread = queue.Queue()
        self.q_from_thread = queue.Queue()
        self.acq_thread = Thread(target=camera_thread, args=(self.camera_type,
                                                             self.q_to_thread,
                                                             self.q_from_thread,
                                                             self.camera_args,
                                                             self.camera_params))
        self.acq_thread.start()

    def acquire(self):
        """Implements the acquire method for an acquisition object.

        Retrieves a frame with the read method, computes the timestamp, publishes the frame data over 0MQ and then
        increments the frame number.
        """
        try:
            data = self.q_from_thread.get_nowait()
        except queue.Empty:
            return
        # Get current time
        t = time.time()
        if isinstance(data, np.ndarray):
            # Broadcast frame data through the network
            self.send_frame(t, self.frame_number, data)
            # Increment the frame index
            self.frame_number += 1
            return
        if isinstance(data, dict):
            self.send_timestamped(t, data)
            return

    def cleanup(self):
        self.q_to_thread.put(("exit", "", (), {}))
        while True:
            try:
                self.q_from_thread.get_nowait()
            except queue.Empty:
                break
        self.acq_thread.join()

    def set_params(self, params, **kwargs):
        if ("target" in kwargs) and (kwargs["target"] != self.name):
            pass
        else:
            self.q_to_thread.put(("event", "set_params", (), params))

    def reset_frame_number(self, **kwargs):
        self.frame_number = 0


CAMERA = {
    "worker": CameraAcquisition,
    "params": {},
    "controller": CameraWidget,
    "plotter": FramePlotter
}
