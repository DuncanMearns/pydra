from pydra_zmq.core.bases import ZMQWorker, ZMQSaver
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


class ProcessMixIn:

    @classmethod
    def start(cls, *args, **kwargs):
        process = PydraProcess(cls, args, kwargs)
        process.start()

    def setup(self):
        return

    def close(self, *args, **kwargs):
        return


class Worker(ZMQWorker, ProcessMixIn):

    name = "worker"

    def __init__(self, process=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._process = process


class Acquisition(Worker):

    name = "acquisition"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _recv(self):
        self.acquire()
        return super()._recv()

    def acquire(self):
        return


class Saver(ZMQSaver, ProcessMixIn):

    name = "saver"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
