from .._base import *
from ..utils import Parallelized


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.events["_events_info"] = self._events_info  # private event to log implemented events

    def _process(self):
        """Handles all messages received over network from ZeroMQ."""
        self.poll()

    # @LOGGED
    # def _events_info(self, **kwargs):
    #     """Logs implemented events."""
    #     return dict(events=[key for key in self.events if not key.startswith("_")])


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
