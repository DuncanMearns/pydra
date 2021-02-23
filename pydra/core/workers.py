from pydra.core.base import PydraObject
from pydra.core.process import ProcessMixIn
from pydra.core.messaging import LOGGED


class Worker(PydraObject, ProcessMixIn):
    """Base worker class. Receives and handles messages. Runs in a separate process.

    Class Attributes
    ----------------
    name : str
        A unique string identifying the worker. Must be specified in all subclasses.
    subscriptions : list of str
        Names of other workers in the network from which this one can receive data and events.
    pipeline : str
        The name of the pipeline to which this worker belongs. Only necessary if there are multiple data streams that
        need to be saved separately.
    plot : iterable
        An iterable of named variables published by the worker that should be plotted in the gui.
    """

    name = "worker"
    subscriptions = []
    pipeline = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events["_test_connection"] = self._check_connection
        self.events["_events_info"] = self._events_info
        self._connected = 0

    def _process(self):
        """Handles all messages received over network from 0MQ."""
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
        return dict(events=[key for key in self.events if not key.startswith("_")])

    def exit(self, *args, **kwargs):
        """Sets the exit_flag when EXIT signal is received, causing process to terminate ."""
        self.close()


class Acquisition(Worker):
    """Base worker class for acquiring data. Implements an independent acquire method after checking for messages."""

    name = "acquisition"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _process(self):
        """Checks for messages received over network from 0MQ, then calls the acquire method."""
        super()._process()
        self.acquire()

    def acquire(self):
        return


# class RemoteReceiver(Worker):
#
#     name = "receiver"
#
#     @classmethod
#     def configure(cls, zmq_config, ports, subscriptions=()):
#         # Create dictionary for storing config info
#         try:
#             assert "receiver" in zmq_config[cls.name]
#         except AssertionError:
#             raise ValueError(f"zmq_config for {cls.name} must contain a 'receiver' key")
#         super(RemoteReceiver, cls).configure(zmq_config, ports, subscriptions)
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#     def poll_remote(self):
#         ret = self.zmq_receiver.poll(0)
#         if ret:
#             parts = self.zmq_receiver.recv_multipart()
#             self.recv_remote(*parts)
#
#     def recv_remote(self, *args):
#         return
#
#     def _process(self):
#         self.poll_remote()
#         super()._process()
#
#
# class RemoteSender(Worker):
#
#     name = "sender"
#
#     @classmethod
#     def configure(cls, zmq_config, ports, subscriptions=()):
#         # Create dictionary for storing config info
#         try:
#             assert "sender" in zmq_config[cls.name]
#         except AssertionError:
#             raise ValueError(f"zmq_config for {cls.name} must contain a 'sender' key")
#         super(RemoteSender, cls).configure(zmq_config, ports, subscriptions)
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
