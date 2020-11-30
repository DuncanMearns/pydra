from pydra_zmq.core.zmq import ZMQWorker
from multiprocessing import Process


class PydraProcess(Process):

    def __init__(self, worker, worker_args, worker_kwargs, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.worker_type = worker
        self.worker_args = worker_args
        self.worker_kwargs = worker_kwargs

    def run(self):
        self.worker = self.worker_type(*self.worker_args, **self.worker_kwargs)
        self.worker.setup()
        while True:
            exit_flag = self.worker._recv()
            if exit_flag:
                break


class Worker(ZMQWorker):

    name = "worker"

    @classmethod
    def start(cls, *args, **kwargs):
        process = PydraProcess(cls, args, kwargs)
        process.start()

    def __init__(self, process=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._process = process
        self.states = {}

    def setup(self):
        return

    def close(self, *args, **kwargs):
        return

    def _recv(self):
        sockets = dict(self.zmq_poller.poll(0))
        for name, sock in self.zmq_subscriptions.items():
            if sock in sockets:
                msg_flag, source, t, flags, *parts = sock.recv_multipart()
                ret = self._handle_event(msg_flag, source, t, flags, *parts)
                return ret
        return


class Acquisition(Worker):

    name = "acquisition"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _recv(self):
        self.acquire()
        return super()._recv()

    def acquire(self):
        return
