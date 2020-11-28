from pydra_zmq.core.zmq import ZMQWorker
from pydra_zmq.core import messaging
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
                self.worker.close()
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

    def close(self):
        return

    def _recv(self):
        sockets = dict(self.zmq_poller.poll())
        for name, sock in self.zmq_subscriptions.items():
            if sock in sockets:
                flag, source, t, *parts = sock.recv_multipart()
                if flag == b"e":
                    return 1
                elif flag == b"m":
                    s = messaging.MESSAGE.serializer().decode(*parts)
                    print(s)
                elif flag == b"s":
                    state, val = messaging.STATE.serializer().decode(*parts)
                    self.set_state(state, val)
        return

    def set_state(self, state, val):
        if state in self.states:
            self.states[state](val)


class Acquisition(Worker):

    name = "acquisition"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _recv(self):
        self.acquire()
        super()._recv()
        return

    def acquire(self):
        return
