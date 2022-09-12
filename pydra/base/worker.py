"""
Module containing basic Worker classes.
"""
import numpy as np

from .pydra_object import *
from .messaging import *
from .parallelized import Parallelized


__all__ = ("Worker", "Acquisition")


class Worker(Parallelized, PydraReceiver, PydraSender):
    """Base worker class.

    Attributes
    ----------
    name : str
        A unique string identifying the worker. Must be specified in all subclasses.
    subscriptions : tuple
        Names of other workers in the network from which this one can receive pydra messages.
    gui_events : tuple of str
        Iterable of event names that should appear in the PydraGUI.
    """

    gui_events = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _process(self):
        """Handles all messages received over pydra network."""
        self.receive_messages()

    @DATA.SEND
    def send_data(self, *args):
        """Generic data sender"""
        return args

    @TIMESTAMPED.SEND
    def send_timestamped(self, t: float, data: dict):
        """Sends timestamped data between objects.

        Parameters
        ----------
        t : float
            The timestamp associated with the data point.
        data : dict
            Dictionary of pickle-able data.
        """
        return t, data

    @INDEXED.SEND
    def send_indexed(self, i: int, t: float, data: dict):
        """Sends indexed data between objects.

        Parameters
        ----------
        i : int
            The index of the data.
        t : float
            A timestamp associated with the given index.
        data : dict
            Dictionary of pickle-able data.
        """
        return i, t, data

    @ARRAY.SEND
    def send_array(self, i: int, t: float, a: np.ndarray):
        """Sends array data between objects.

        Parameters
        ----------
        i : int
            The index of the data.
        t : float
            A timestamp associated with the given index.
        a : np.ndarray
            A numpy array containing data.
        """
        return i, t, a

    @FRAME.SEND
    def send_frame(self, i: int, t: float, frame: np.ndarray):
        """Sends frama data between objects.

        Parameters
        ----------
        i : int
            The index of the frame.
        t : float
            The timestamp of the frame.
        frame : np.ndarray
            A numpy array containing data.
        """
        return i, t, frame


class Acquisition(Worker):
    """Base worker class for acquiring data. Implements an independent acquire method after checking for messages."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _process(self):
        """Checks for messages received over network from ZeroMQ, then calls the acquire method."""
        super()._process()
        self.acquire()

    def acquire(self):
        return
