from .._base import *
from ..messaging import *
from ..utils.states import NotConnected, SetupFinished
from .backend import PydraBackend
from .worker import Worker
import zmq
import warnings
import logging
from datetime import datetime
import time


class PydraMain(PydraReceiver, PydraPublisher, PydraSubscriber):

    config = {}

    def __init__(self, connections: dict = None, modules: list = (), savers: list = ()):
        self.connections = connections or self.config["connections"]["pydra"]
        self.savers = savers
        self.modules = modules or self.config["modules"]
        super().__init__(**self.connections)
        self._backend = None
        self._workers = []
        self._setup_state = NotConnected(self)

    @property
    def savers(self):
        return self._savers

    @savers.setter
    def savers(self, args):
        self._savers = list(args)
        if not args:
            self._savers = list(self.config["savers"])
            for saver in self._savers:
                saver._connections = self.config["connections"][saver.name]

    def setup(self):
        self._setup_state = self._setup_state()
        while not isinstance(self._setup_state, SetupFinished):
            self.poll()
            self._setup_state = self._setup_state()

    def start_backend(self, connections: dict = None):
        # Start saver and wait for it to respond
        connections = connections or self.config["connections"]["backend"]
        saver_tuples = tuple(saver.to_tuple() for saver in self.savers)
        self._backend = PydraBackend.start(saver_tuples, **connections)

    def load_module(self, idx):
        try:
            module = self.modules[idx]
        except IndexError:
            return False, None
        worker = module["worker"]
        params = module.get("params", {})
        threaded = module.get("threaded", False)
        self.start_worker(worker, params, as_thread=threaded)
        return True, worker.name

    def start_worker(self, worker: Worker, params: dict = None, connections: dict = None, as_thread=False):
        # Create dict for instantiating worker in new process/thread
        params = params or {}
        connections = connections or self.config["connections"][worker.name]
        kw = params.copy()
        kw.update(connections)
        # Start process
        if as_thread:
            process = worker.start_thread(**kw)
        else:
            process = worker.start(**kw)
        # Add to workers
        self._workers.append(process)

    @ERROR.callback
    def handle_error(self, error, message, **kwargs):
        source = kwargs["source"]
        t = kwargs["timestamp"]
        error_info = f"{source} raised {repr(error)}: {datetime.fromtimestamp(t)}.\n"
        logging.error(error_info + message)

    handle__error = handle_error

    @CONNECTION.callback
    def handle_connection(self, ret, **kwargs):
        t = kwargs["timestamp"]
        self._setup_state.connections[kwargs["source"]] = ret, t

    handle__connection = handle_connection

    @REQUEST
    def fetch_data(self):
        return "data",

    @_DATA.callback
    def handle__data(self, *args, **kwargs):
        pass

    @EXIT
    def _exit(self):
        """Broadcasts an exit signal."""
        return ()

    def exit(self):
        """Ends and joins worker process for proper exiting."""
        print("Exiting...")
        self._exit()
        print("Cleaning up connections...")
        for process in self._workers:
            process.join()
            print(f"Worker {process.worker_type.name} joined")
        try:
            self._backend.join()
            print("Backend joined.")
        except AttributeError:
            pass

    @staticmethod
    def destroy():
        """Destroys the ZeroMQ context."""
        zmq.Context.instance().destroy(200)
