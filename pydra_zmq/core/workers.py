from .bases import ZMQWorker, ProcessMixIn


class Worker(ZMQWorker, ProcessMixIn):

    name = "worker"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _process(self):
        self._recv()

    def exit(self, *args, **kwargs):
        self.close()


class Acquisition(Worker):

    name = "acquisition"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _process(self):
        self._recv()
        self.acquire()

    def acquire(self):
        return
