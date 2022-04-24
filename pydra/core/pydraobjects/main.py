from .._base import *
from .saver import PydraBackend, QUERY
from .worker import Worker
import zmq
import warnings
import time


class PydraMain(PydraReceiver, PydraPublisher, PydraSubscriber):

    name = "pydra"
    config = {}

    def __init__(self, connections: dict = None):
        self.connections = connections or self.config["connections"]["pydra"]
        super().__init__(**self.connections)
        self.msg_callbacks["connection"] = self._worker_connected
        self._backend = None
        self._workers = []
        self._connected = {}

    def start_savers(self, savers=(), connections: dict = None):
        # Start saver and wait for it to respond
        connections = connections or self.config["connections"]["interface"]
        if not savers:
            savers = self.config["savers"]
            for saver in savers:
                saver._connections = self.config["connections"][saver.name]
        saver_tuples = [saver.to_tuple() for saver in savers]
        self._backend = PydraBackend.start(saver_tuples, **connections)
        for t in range(3):
            time.sleep(1.)
        print("sending backend test")
        self.backend_test()
        return True

    def start_worker(self, worker: Worker, params: dict = None, connections: dict = None, as_thread=False,
                     test_connection=False, timeout=10.):
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
        if test_connection:
            self.network_test(timeout=timeout)
        return True

    def network_test(self, timeout=10.):
        """Checks that all workers in the network are receiving messages from pydra.

        Parameters
        ----------
        timeout : float
            Maximum time to wait for workers to respond (seconds).
        """
        print("Testing connections...")
        # Get the current time and timeout time
        t0 = time.time()
        t_timeout = t0 + timeout
        # Create a dictionary with the connection status of each worker
        self._nettest_t0 = t0
        self._connected = dict([(process.worker_type.name, False) for process in self._workers])
        # Send test connection event
        while (time.time() < t_timeout) and (not all(self._connected.values())):
            self.send_event("_test_connection")
            self.poll()
        # Check whether all modules connected
        passed = True
        for name in self._connected:
            if not self._connected[name]:
                warnings.warn(f"Module {name} did not respond within {timeout} seconds. Check connections in config.")
                passed = False
        if passed:
            print(f"All modules passed network test within {time.time() - t0:.2f} seconds.")

    @QUERY
    def backend_test(self):
        return "connected"

    @CONNECTION.callback
    def _worker_connected(self, ret, **kwargs):
        self._connected[kwargs["source"]] = ret
        if ret:
            print(f"{kwargs['source']} responsed in {kwargs['timestamp'] - self._nettest_t0:.2f} seconds.")

    def handle_qm(self, **kwargs):
        print(kwargs)

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
            print("Saver joined.")
        except AttributeError:
            pass

    @staticmethod
    def destroy():
        """Destroys the ZeroMQ context."""
        zmq.Context.instance().destroy(200)
