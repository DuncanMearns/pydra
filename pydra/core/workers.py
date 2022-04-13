from pydra.core.base import *
from pydra.core.process import ProcessMixIn
from pydra.core.messaging import LOGGED


class Worker(ProcessMixIn, PydraPublisher, PydraSubscriber):
    """Base worker class. Receives and handles messages. Runs in a separate process.

    Attributes
    ----------
    name : str
        A unique string identifying the worker. Must be specified in all subclasses.
    subscriptions : tuple
        Names of other workers in the network from which this one can receive data and events.
    pipeline : str
        The name of the pipeline to which this worker belongs. Only necessary if there are multiple data streams that
        need to be saved separately.
    """

    name = "worker"
    subscriptions = ()
    pipeline = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events["_test_connection"] = self._check_connection  # private event to test zmq connections
        self.events["_events_info"] = self._events_info  # private event to log implemented events
        self._connected = 0

    def _process(self):
        """Handles all messages received over network from ZeroMQ."""
        self.poll()

    def _check_connection(self, **kwargs):
        """Called by the 'test_connection' event. Informs pydra that 0MQ connections have been established and worker is
        receiving messages."""
        if not self._connected:
            self._connected = 1
            self.connected()

    @LOGGED
    def connected(self):
        """Logs that worker has received the 'test_connection' event."""
        return dict()

    @LOGGED
    def _events_info(self, **kwargs):
        """Logs implemented events."""
        return dict(events=[key for key in self.events if not key.startswith("_")])

    def exit(self, *args, **kwargs):
        """Sets the exit_flag when EXIT signal is received, causing process to terminate."""
        self.close()


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
