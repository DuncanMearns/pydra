from .._base import *
from ._runner import Parallelized


class Worker(Parallelized, PydraPublisher, PydraSubscriber):
    """Base worker class.

    Attributes
    ----------
    name : str
        A unique string identifying the worker. Must be specified in all subclasses.
    subscriptions : tuple
        Names of other workers in the network from which this one can receive pydra messages.
    """

    name = "worker"
    subscriptions = ()
    gui_events = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _process(self):
        """Handles all messages received over network from ZeroMQ."""
        self.poll()


class Acquisition(Worker):
    """Base worker class for acquiring data. Implements an independent acquire method after checking for messages."""

    name = "acquisition"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _process(self):
        """Checks for messages received over network from ZeroMQ, then calls the acquire method."""
        super()._process()
        self.acquire()

    def acquire(self):
        return
