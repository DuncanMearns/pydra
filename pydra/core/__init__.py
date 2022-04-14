from .base import *
from .saving import PydraSaver
from .workers import Worker, Acquisition
# from .protocol import Protocol, Trigger
import zmq
import warnings


class PydraMain(PydraReceiver, PydraPublisher, PydraSubscriber):

    name = "pydra"
    config = {}

    def __init__(self, connections: dict = None):
        self.connections = connections or self.config["connections"]["pydra"]
        super().__init__(**self.connections)
        self.msg_handlers["connection"] = self._worker_connected
        self._workers = []
        self._connected = {}

    def start_saver(self, connections: dict = None):
        # Start saver and wait for it to respond
        connections = connections or self.config["connections"]["saver"]
        # self.saver = PydraSaver.start(self.pipelines, connections=connections)
        # self.zmq_receiver.recv_multipart()
        return True

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
        self.test_connections((process,))
        # Add to workers
        self._workers.append(process)
        return True

    def test_connections(self, processes=(), timeout=10.):
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
        processes = processes or self._workers
        test_workers = dict([(process.worker_type.name, False) for process in processes])
        self._connected.update(test_workers)
        # Send test connection event
        while (time.time() < t_timeout) and (not all(self._connected.values())):
            self.send_event("_test_connection")
            self.poll()
        # Check whether all modules connected
        passed = True
        for name in test_workers:
            if not self._connected[name]:
                warnings.warn(f"Module {name} did not respond within {timeout} seconds. Check connections in config.")
                passed = False
        if passed:
            print(f"All modules passed connection test within {time.time() - t0:.2f} seconds.")

    @CONNECTION.recv
    def _worker_connected(self, ret, **kwargs):
        self._connected[kwargs["source"]] = ret

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
            self.saver.join()
            print("Saver joined.")
        except AttributeError:
            pass
        # self._exiting.emit()

    @staticmethod
    def destroy():
        """Destroys the ZeroMQ context."""
        zmq.Context.instance().destroy(200)
