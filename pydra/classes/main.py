from .._base import *
from ..messaging import *
from ._setup import SetupStateMachine
from .backend import PydraBackend
from .worker import Worker

import zmq
import logging
from datetime import datetime


class PydraMain(PydraReceiver, PydraPublisher, PydraSubscriber):
    """The singleton main pydra class, implementing network initialization and front/backend connections. May be further
    subclassed.

    Parameters
    ----------
    connections : dict
        Connections dictionary. Overrides default config in config class attribute.
    modules : list
        List of modules. Overrides default config in config class attribute.
    savers : list
        List of savers. Overrides default config in config class attribute.

    Attributes
    ----------
    config : dict
        Class attribute. The default setup configuration. Can be overridden through __init__.
    connections : dict
        Copy of connections parameter, or from config.
    modules : list
        Copy of modules parameter, or from config.
    savers : list
        Copy of savers parameter, or from config with connections initialized.
    _backend : PydraBackend
        The PydraBackend instance.
    _workers : list
        List of instantiated worker processes/threads.
    _setup_state : SetupState
        Instance of SetupState. Updates during setup method call, ensuring network initializes properly.
    """

    config = {}

    def __init__(self, connections: dict = None, modules: list = (), savers: list = ()):
        self.connections = connections or self.config["connections"]["pydra"]
        self.savers = savers
        self.modules = modules or self.config["modules"]
        super().__init__(**self.connections)
        self._backend = None
        self._workers = []
        self._connection_times = {}
        self._state_machine = SetupStateMachine(self)

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
        while not self._state_machine.finished:
            self.poll()
            self._state_machine.update()

    def start_backend(self, connections: dict = None):
        # Start saver and wait for it to respond
        connections = connections or self.config["connections"]["backend"]
        savers = [saver.to_constructor() for saver in self.savers]
        self._backend = PydraBackend.start(tuple(savers), **connections)

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
        self._connection_times[kwargs["source"]] = ret, t

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
