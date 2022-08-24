from .._base import PydraReceiver, PydraPublisher, PydraSender, PydraSubscriber
from ..messaging import *
from ._runner import Parallelized


__all__ = ("PydraBackend",)


class PydraBackend(Parallelized, PydraReceiver, PydraPublisher, PydraSender, PydraSubscriber):
    """Singleton backend class that acts as interface between main pydra class and savers.

    Parameters
    ----------
    savers : tuple
        A tuple of saver constructor objects, allows saver objects to be instantiated in new threads/processes while
        preserving modifications to class attributes.

    Attributes
    ----------
    event_callbacks : dict
        Dictionary containing callback methods for event messages.
    savers : list
        Tuple of saver constructors running in the backend.
    _threads : list
        List of running saver threads.
    _saver_connections : dict
        Tracks whether saver objects have successfully connected to zmq sockets. Automatically updated by _CONNECTION
        message callback.
    """

    name = "backend"

    def __init__(self, savers=(), *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Savers
        self.savers = savers
        self._threads = []
        self._saver_connections = {}

    def setup(self):
        """Start saver threads."""
        for constructor in self.savers:
            new_cls = constructor()  # generate the saver class by calling the constructor
            thread = new_cls.start()  # instantiate saver in new thread
            self._threads.append(thread)  # add to list of open threads
            self._saver_connections[new_cls.name] = False  # add unconnected saver to connections dict

    @property
    def _savers_connected(self):
        """Returns True when all savers are connected to zmq sockets, otherwise False."""
        return all(self._saver_connections.values())

    @BACKEND.CONNECTION
    def connected(self):
        return self._savers_connected,

    @BACKEND.CONNECTION.callback
    def handle__connection(self, ret, **kwargs):
        """Callback for _CONNECTION messages from savers. Updates the _saver_connections dictionary."""
        self._saver_connections[kwargs["source"]] = ret

    @BACKEND.ERROR.callback
    def handle__error(self, error, message, **kwargs):
        self.raise_error(error, message)

    def _process(self):
        """Receive messages."""
        self.poll()

    @EXIT
    def _exit(self):
        """Broadcasts exit signal to savers."""
        return ()

    def reply_data(self):
        self.send_request("data")

    @BACKEND.FORWARD
    def handle__data(self, data, **kwargs):
        """Receives requested data from savers."""
        return data, kwargs

    def exit(self, *args, **kwargs):
        """Terminates the process loop."""
        # if self.recording:
        #     self.stop_recording()
        print("Backend exiting...")
        self._exit()
        for thread in self._threads:
            thread.join()
        super().exit()

    def start_recording(self, directory: str = None, filename: str = None, **kwargs):
        """Implements a start_recording event. Starts saving data."""
        print("START RECORDING")
        self.send_event("start_recording", directory=directory, filename=filename)

    def stop_recording(self, **kwargs):
        """Implements a stop_recording event. Stops saving data."""
        print("STOP RECORDING")
        self.send_event("stop_recording")
