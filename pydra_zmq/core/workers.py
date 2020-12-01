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
        self.worker.run()


class ProcessMixIn:

    @classmethod
    def start(cls, *args, **kwargs):
        process = PydraProcess(cls, args, kwargs)
        process.start()


class Worker(ZMQWorker, ProcessMixIn):

    name = "worker"

    def __init__(self, process=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._process = process
        self.exit_flag = 0
        # if save:
        #     self.recording = 0
        #     self.states["recording"] = self.record
            # self.events["start_record"] = self.start_record

    def setup(self):
        return

    def close(self, *args, **kwargs):
        self.exit_flag = 1

    def run(self):
        self.setup()
        while not self.exit_flag:
            self._recv()

    # def record(self, val, **kwargs):
    #     self.recording = val
        # if val:


class Acquisition(Worker):

    name = "acquisition"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _recv(self):
        super()._recv()
        self.acquire()

    def acquire(self):
        return


class Saver(ZMQSaver, ProcessMixIn):

    name = "saver"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events["set_working_directory"] = self.set_working_directory
        self.events["set_filename"] = self.set_filename
        self.events["start_record"] = self.start_record
        # Set the working directory
        self.working_dir = None
        self.filename = None

    def set_working_directory(self, directory=None, **kwargs):
        self.working_dir = directory
        return 1

    def set_filename(self, filename=None, **kwargs):
        self.filename = filename
        return 1

    def start_record(self, **kwargs):
        # while True:
        #     print(self.save_from)
        #     break
        return 1

    def record(self, val, **kwargs):
        return
