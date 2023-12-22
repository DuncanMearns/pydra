from .base import *
from .configuration import Configuration, pydra_tuple
from .protocol.triggers import Trigger, TriggerCollection

import sys
import zmq
import logging
from datetime import datetime
import time
from threading import Lock
from typing import Iterable, Mapping


class Pydra(PydraReceiver, PydraSender):
    """The main Pydra class.

    Parameters
    ----------
    workers : iterable of pydra_tuples
        Iterable of tuples: (name, class, args, kwargs).
    savers : iterable of pydra_tuples
        Iterable of tuples: (name, class, args, kwargs).
    triggers : mapping
        Mapping of trigger_name, trigger_object pairs.
    """

    name = "pydra"
    config = Configuration()

    RUNNING = 1
    ENDED = 0

    @staticmethod
    def run(config: Configuration = None, **kwargs):
        """Return an instantiated Pydra object with the current configuration."""
        if not config:
            config = Configuration(**kwargs)
        if not isinstance(config, Configuration):
            raise TypeError("config must be a valid Configuration")
        Pydra.config = config
        connections = config.connections["pydra"]
        workers = config.workers
        savers = config.savers
        triggers = config.triggers
        pydra = Pydra(workers, savers, triggers, **connections)
        pydra.setup()
        return pydra

    def __init__(self,
                 workers: Iterable[pydra_tuple] = (),
                 savers: Iterable[pydra_tuple] = (),
                 triggers: Mapping[str, Trigger] = None,
                 **connections):
        super().__init__(**connections)
        self.workers = workers
        self.savers = savers
        self.triggers = triggers or {}
        self._saver_processes = {}
        self._worker_processes = {}
        self._connection_times = {}
        self._running_flag = self.RUNNING
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
        """Initialize the pydra network."""
        # Start triggers
        self.triggers.start()
        # Start savers
        self._saver_processes = self.spawn_processes(*self.savers)
        self.wait_for_connections([saver.name for saver in self.savers])
        # Start workers
        for worker in self.workers:
            _process_dict = self.spawn_processes(worker)
            self._worker_processes.update(_process_dict)
            self.wait_for_connections(_process_dict.keys())
        # self._worker_processes = self.spawn_processes(*self.workers)
        # self.wait_for_connections([worker.name for worker in self.workers])

    @staticmethod
    def spawn_processes(*pydra_tuples: pydra_tuple):
        """Spawn process containing other pydra objects."""
        process_dict = {}
        for (name, pydra_cls, args, kwargs) in pydra_tuples:
            process = spawn_new(pydra_cls, args, kwargs)
            process_dict[name] = process
        return process_dict

    def wait_for_connections(self, names):
        """Wait until connected signals have been received from named pydra objects."""
        t0 = time.time()
        for name in names:
            print(f"connecting to {name}\n")
        while True:
            connected = [self.check_connected(name) for name in names]
            if all(connected):
                break
            self.send_event("_test_connection")
            self.receive_messages(50)
        if not self.is_running():
            return
        for name in names:
            t = self._connection_times[name]
            print(f"{name} connected in {t - t0:.2f} seconds.\n")

    def check_connected(self, name):
        """Check if named pydra object is connected to the network."""
        return name in self._connection_times

    def process_connected(self, source, t):
        if source not in self._connection_times:
            self._connection_times[source] = t

    @EXIT.SEND
    def _exit(self):
        """Broadcasts an exit signal."""
        return ()

    @CONNECTION.CALLBACK
    def handle_connection(self, **kwargs):
        """Connection handler"""
        source = kwargs["source"]
        t = kwargs["timestamp"]
        self.process_connected(source, t)

    @ERROR.CALLBACK
    def handle_error(self, error, message, critical, **kwargs):
        """Error handler"""
        source = kwargs["source"]
        t = kwargs["timestamp"]
        error_info = f"{source} raised {repr(error)}: {datetime.fromtimestamp(t)}.\n"
        logging.error(error_info + message)
        if critical:
            self.exit()
            sys.exit(-1)
        self.process_connected(source, t)

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
        messages = self.poll()  # flush cache
        print(len(messages), "unprocessed messages.")
        self.receive_messages()
        self._running_flag = self.ENDED

    def send_event(self, event_name, **kwargs):
        """Broadcasts an event to the network (thread-safe)."""
        with self.zmq_lock:
            super().send_event(event_name, **kwargs)

    @staticmethod
    def destroy():
        """Destroys the ZeroMQ context."""
        zmq.Context.instance().destroy(200)

    def is_running(self):
        """Perform a check if the exit signal has been sent."""
        return self._running_flag == self.RUNNING
