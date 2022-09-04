from ._base import *
from .messaging import *
from .configuration import Configuration
from .classes import PydraBackend, Worker
from .protocol import TriggerThread
from .utils.state import state_descriptor

import zmq
import logging
from datetime import datetime
import time
from threading import Lock


setup_state = state_descriptor.new_type("setup_state")


class SetupStateMachine:
    """Class for setting up Pydra. Handles different setup states and ensures each process/thread is connected."""

    not_connected = setup_state(0)
    connecting = setup_state(1)
    finished = setup_state(2)

    def __init__(self, pydra):
        self.pydra = pydra
        self.t0 = 0
        self.module_idx = 0
        self.module_name = ""
        self.not_connected()

    def update(self):
        if self.not_connected:
            self.start_backend()
        if self.connecting:
            self.wait()

    def start_backend(self):
        print("Connecting to backend...")
        self.t0 = time.time()
        self.pydra.start_backend()
        self.module_name = "backend"
        self.connecting()

    def wait(self):
        connected, t = self.get_connected()
        if connected:
            print(f"{self.module_name} connected in {t - self.t0:.2f} seconds.\n")
            self.start_worker()
            return
        self.pydra.send_event("_test_connection")
        time.sleep(0.01)

    def start_worker(self):
        exists, name = self.pydra.load_module(self.module_idx)
        if exists:
            self.t0 = time.time()
            self.module_name = name
            self.module_idx += 1
            print(f"Connecting to {self.module_name}...")
            return
        self.finished()
        print("All modules connected.\n")

    def get_connected(self):
        return self.pydra._connection_times.get(self.module_name, (False, 0))


class TriggerCollection:

    def __init__(self, triggers: dict):
        self.triggers = triggers
        self.threads = {}

    def start(self):
        for name, trigger in self.triggers.items():
            thread = TriggerThread(trigger)
            thread.start()
            self.threads[name] = thread

    def close(self):
        for name, thread in self.threads.items():
            thread.terminate()
            thread.join()
            print(f"Trigger {name} joined.")

    def __getitem__(self, item):
        return self.threads[item]


def blocking(method):
    def blocked(pydra_instance, *args, **kwargs):
        with pydra_instance.event_lock:
            ret = method(pydra_instance, *args, **kwargs)
        return ret
    return blocked


class Pydra(PydraReceiver, PydraPublisher, PydraSubscriber):
    """The singleton main pydra class, implementing network initialization and front/backend connections.

    Parameters
    ----------
    connections : dict
        Connections dictionary. Overrides default config in config class attribute.
    modules : list
        List of modules. Overrides default config in config class attribute.
    savers : list
        List of savers. Overrides default config in config class attribute.

    Attributes
    ----------------
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
    _state_machine : SetupStateMachine
        Instance of SetupStateMachine. Updates during setup method call, ensuring network initializes properly.
    """

    name = "pydra"
    config = Configuration()

    @staticmethod
    def run(config: Configuration = None, *,
            modules=(), savers=(), triggers=(), connections: dict = None, public=None, private=None):
        """Return an instantiated Pydra object with the current configuration."""
        if not config:
            config = Configuration(modules=modules, triggers=triggers,
                                   _connections=connections, _public_ports=public, _private_ports=private)
        if not isinstance(config, Configuration):
            raise TypeError("config must be a valid Configuration")
        Pydra.config = config
        pydra = Pydra()
        pydra.setup()
        return pydra

    def __init__(self, connections: dict = None, modules: list = (), savers: list = (), triggers: list = ()):
        self.connections = connections or self.config["connections"]["pydra"]
        self.modules = modules or self.config["modules"]
        self.savers = savers
        self.triggers = triggers or self.config["triggers"]
        super().__init__(**self.connections)
        self._backend = None
        self._workers = []
        self._connection_times = {}
        self._state_machine = SetupStateMachine(self)
        self.event_lock = Lock()
        self.triggers.start()

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

    @property
    def triggers(self):
        return self._triggers

    @triggers.setter
    def triggers(self, d: dict):
        self._triggers = TriggerCollection(d)

    def setup(self):
        while not self._state_machine.finished:
            self.poll(1)
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
        worker = module.worker
        params = module.params
        threaded = module.threaded
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

    @BACKEND.FORWARD.callback
    def handle__forward(self, data, origin, **kwargs):
        self.receive_data(data, **origin)

    @BACKEND.DATA.callback
    def receive_data(self, data, **kwargs):
        return data, kwargs

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
            raise ValueError("Backend does not exist?")
        self.triggers.close()

    @staticmethod
    def destroy():
        """Destroys the ZeroMQ context."""
        zmq.Context.instance().destroy(200)

    @blocking
    def send_event(self, event_name, **kwargs):
        super().send_event(event_name, **kwargs)

    @blocking
    def send_request(self, what: str):
        super().send_request(what)
