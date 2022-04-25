from .._base import PydraReceiver, PydraPublisher, PydraSender, PydraSubscriber
from ..messaging import _CONNECTION, EXIT
from ..utils import Parallelized


class PydraBackend(Parallelized, PydraReceiver, PydraPublisher, PydraSender, PydraSubscriber):
    """Singleton Saver class that integrates and handles incoming messages from all workers.

    Parameters
    ----------
    connections : dict
        Dictionary of workers (as a list of names) assigned to each pipeline (keys). Passed from pydra pipelines
        property.

    Attributes
    ----------
    event_log : list
        Logged messages from pydra objects.
    messages : list
        List of string-type messages received from pydra objects.
    recording : bool
        Stores whether data are currently being saved.
    savers : list
        List that stores all PipelineSaver objects.
    targets : dict
        A dictionary that maps data received from workers to the appropriate PipelineSaver object.
    """

    name = "backend"

    def __init__(self, savers=(), *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Recording events
        self.event_callbacks["start_recording"] = self.start_recording
        self.event_callbacks["stop_recording"] = self.stop_recording
        # Savers
        self.savers = savers
        self._threads = []
        self._saver_connections = {}

    def setup(self):
        """Start saver threads."""
        for cls_type, args, kwargs, connections in self.savers:
            new_cls = type(cls_type.name, (cls_type,), {"args": args, "kwargs": kwargs, "_connections": connections})
            thread = new_cls.start()
            self._threads.append(thread)
            self._saver_connections[new_cls.name] = False

    @property
    def _savers_connected(self):
        return all(self._saver_connections.values())

    @_CONNECTION
    def connected(self):
        return self._savers_connected,

    @_CONNECTION.callback
    def handle__connection(self, ret, **kwargs):
        self._saver_connections[kwargs["source"]] = ret

    def _process(self):
        """Receive messages from workers."""
        self.poll()

    @EXIT
    def _exit(self):
        """Broadcasts an exit signal."""
        return ()

    def exit(self, *args, **kwargs):
        """Terminates the process loop."""
        # if self.recording:
        #     self.stop_recording()
        self._exit()
        for thread in self._threads:
            thread.join()
        super().exit()

    def start_recording(self, directory: str = None, filename: str = None, **kwargs):
        """Implements a start_recording event. Starts saving data."""
        print("START RECORDING")
        # if not self.recording:
        #     for pipeline in self.savers:
        #         pipeline.start(directory, filename)
        #     self.recording = True

    def stop_recording(self, **kwargs):
        """Implements a stop_recording event. Stops saving data."""
        print("STOP RECORDING")
        # if self.recording:
        #     for pipeline in self.savers:
        #         pipeline.stop()
        #     self.recording = False
