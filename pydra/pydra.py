from ._base import *
from .messaging import *
from .classes import PydraBackend, Worker
from .utils.state import state_descriptor

import pydra.configuration as configuration
import zmq
import logging
from datetime import datetime
import time
from threading import Lock
import os


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


def blocking(method):
    def blocked(pydra_instance, *args, **kwargs):
        with pydra_instance.event_lock:
            ret = method(pydra_instance, *args, **kwargs)
        return ret
    return blocked


class Pydra(PydraReceiver, PydraPublisher, PydraSubscriber):
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
    config = {}

    @staticmethod
    def run(modules=(), savers=(), config: dict = None, public=None, private=None):
        """Return an instantiated Pydra object with the current configuration."""
        Pydra.configure(modules, savers, config, public, private)
        pydra = Pydra()
        pydra.setup()
        return pydra

    def __init__(self, connections: dict = None, modules: list = (), savers: list = ()):
        self.connections = connections or self.config["connections"]["pydra"]
        self.savers = savers
        self.modules = modules or self.config["modules"]
        super().__init__(**self.connections)
        self._backend = None
        self._workers = []
        self._connection_times = {}
        self._state_machine = SetupStateMachine(self)
        self.event_lock = Lock()
        self.working_dir = self.config.get("default_directory", os.getcwd())
        self.filename = self.config.get("default_filename", "")
        self.recording_idx = 0

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

    @FORWARD.callback
    def handle__forward(self, data, origin, **kwargs):
        self.receive_data(data, **origin)

    @_DATA.callback
    def receive_data(self, data, **kwargs):
        return data

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

    @blocking
    def send_event(self, event_name, **kwargs):
        super().send_event(event_name, **kwargs)

    def start_recording(self):
        """Broadcasts a start_recording event."""
        directory = str(self.working_dir)
        filename = str(self.filename)
        idx = int(self.recording_idx)
        self.send_event("start_recording", directory=directory, filename=filename, idx=idx)

    def stop_recording(self):
        """Broadcasts a start_recording event."""
        self.send_event("stop_recording")

    @staticmethod
    def configure(modules=(),
                  savers=(),
                  config: dict = None,
                  public: configuration.PortManager = None,
                  private: configuration.PortManager = None):
        """Generates a configuration dictionary (stored in config class attribute).

        Parameters
        ----------
            modules : tuple
                List of modules to include in configuration.
            savers : tuple
                List of savers to include in configuration.
            config : dict (optional)
                A pre-configured dictionary.
            public : configuration.PortManager (optional)
                Ports to use for frontend zmq connections.
            private : configuration.PortManager (optional)
                Ports to use for backend zmq connections.
        """

        config = config or configuration.config
        public = public or configuration.ports
        private = private or configuration._ports

        # Get backend ports
        pub, sub = private.next()
        send, recv = private.next()
        bpub, bsub = private.next()

        # Initialize backend configuration
        pydra_config = configuration.PydraConfig("pydra", pub, sub)
        backend_config = configuration.BackendConfig("backend", send, recv, bpub, bsub)
        backend_config.add_subscription(pydra_config, (EXIT, EVENT, REQUEST))
        pydra_config.add_receiver(backend_config)

        # Set/get modules
        if modules:
            config["modules"] = list(modules)
        else:
            modules = config["modules"]

        # Initialize worker configuration
        worker_configs = {}
        for module in modules:
            name = module["worker"].name
            pub, sub = public.next()
            worker_config = configuration.WorkerConfig(name, pub, sub)
            # Add worker to configs
            worker_configs[name] = worker_config

        # Handle worker subscriptions
        for module in modules:
            name = module["worker"].name
            worker_config = worker_configs[name]
            # Add subscription to pydra
            worker_config.add_subscription(pydra_config, (EXIT, EVENT))
            # Add to pydra subscriptions
            pydra_config.add_subscription(worker_config, (CONNECTION, ERROR))
            # Add subscriptions to other workers
            for other in module["worker"].subscriptions:
                other_config = worker_configs[other.name]
                worker_config.add_subscription(other_config, (EVENT, DATA, STRING, TRIGGER))

        # Set/get savers
        if savers:
            config["savers"] = list(savers)
        else:
            savers = config["savers"]

        # Configure savers
        saver_configs = {}
        for saver in savers:
            send, recv = private.next()
            saver_config = configuration.SaverConfig(saver.name, send, recv)
            saver_config.add_subscription(backend_config, (EXIT, EVENT, REQUEST))
            for worker_name in saver.workers:
                saver_config.add_subscription(worker_configs[worker_name], (EVENT, DATA, STRING, TRIGGER))
            backend_config.add_receiver(saver_config)
            saver_configs[saver.name] = saver_config

        all_configs = [pydra_config, backend_config]
        all_configs.extend(worker_configs.values())
        all_configs.extend(saver_configs.values())
        config["connections"] = dict([(cfg.name, cfg.connections) for cfg in all_configs])

        # Set the config attribute
        Pydra.config = config
        return Pydra
