from ._base import *
from .messaging import *
from .configuration import Configuration, worker_tuple
from .classes import spawn_new, WorkerFactory
from .protocol.triggers import TriggerCollection

import zmq
import logging
from datetime import datetime
import time
from threading import Lock
import typing


def blocking(method):
    def blocked(pydra_instance, *args, **kwargs):
        with pydra_instance.zmq_lock:
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
    savers : list
        Copy of savers parameter, or from config with connections initialized.
    _worker_processes : list
        List of instantiated worker processes/threads.
    """

    name = "pydra"
    config = Configuration()

    @staticmethod
    def run(config: Configuration = None, *, modules=(), triggers=(),
            connections: dict = None, public=None, private=None):
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

    def __init__(self,
                 workers: typing.Iterable[worker_tuple] = (),
                 savers: typing.Iterable[worker_tuple] = (),
                 triggers: typing.Iterable = (),
                 connections: typing.Mapping = None):
        self.workers = workers or self.config["workers"]
        self.savers = savers or self.config["savers"]
        self.triggers = triggers or self.config["triggers"]
        self.connections = connections or self.config["connections"]["pydra"]
        super().__init__(**self.connections)
        self._saver_processes = {}
        self._worker_processes = {}
        self._connection_times = {}
        self.zmq_lock = Lock()

    @property
    def modules(self):
        return self.config.modules

    @property
    def triggers(self):
        return self._triggers

    @triggers.setter
    def triggers(self, d: dict):
        self._triggers = TriggerCollection(d)

    def setup(self):
        # Start triggers
        self.triggers.start()
        # Start savers
        self._saver_processes = self.spawn_processes(*self.savers)
        self.wait_for_connections([saver.name for saver in self.savers])
        # Start workers
        self._worker_processes = self.spawn_processes(*self.workers)
        self.wait_for_connections([worker.name for worker in self.workers])

    @staticmethod
    def spawn_processes(*worker_tuples):
        process_dict = {}
        for (name, pydra_cls, args, kwargs) in worker_tuples:
            factory = WorkerFactory.from_worker(pydra_cls)
            process = spawn_new(factory, args, kwargs)
            process_dict[name] = process
        return process_dict

    def wait_for_connections(self, names):
        t0 = time.time()
        for name in names:
            print(f"connecting to {name}")
        while True:
            connected = [self.check_connected(name) for name in names]
            if all(connected):
                break
            self.send_event("_test_connection")
            self.poll(10)
        for name in names:
            conn, t = self._connection_times[name]
            print(f"{name} connected in {t - t0:.2f} seconds.\n")

    def check_connected(self, name):
        return name in self._connection_times

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

    @BACKEND.DATA.callback
    def handle__data(self, data, **kwargs):
        """Receives requested data from savers."""
        self.receive_data(data, **kwargs)

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
        for name, process in self._worker_processes.items():
            process.join()
            print(f"Worker {name} joined.")
        for name, process in self._saver_processes.items():
            process.join()
            print(f"Worker {name} joined.")
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
