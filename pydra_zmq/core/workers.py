from pydra_zmq.core.bases import ZMQWorker, ZMQSaver
from pydra_zmq.core.serialize import *
from multiprocessing import Process
import zmq


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exit_flag = 0

    @classmethod
    def start(cls, *args, **kwargs):
        process = PydraProcess(cls, args, kwargs)
        process.start()

    def close(self):
        self.exit_flag = 1

    def setup(self):
        return

    def _process(self):
        return

    def run(self):
        self.setup()
        while not self.exit_flag:
            self._process()


class Worker(ZMQWorker, ProcessMixIn):

    name = "worker"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # if save:
        #     self.recording = 0
        #     self.states["recording"] = self.record
            # self.events["start_record"] = self.start_record

    def _process(self):
        self._recv()

    def exit(self, *args, **kwargs):
        self.close()

    # def record(self, val, **kwargs):
    #     self.recording = val
        # if val:


class Acquisition(Worker):

    name = "acquisition"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _process(self):
        self._recv()
        self.acquire()

    def acquire(self):
        return


class Saver(ZMQSaver, ProcessMixIn):

    name = "saver"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Message cache
        self.messages = []
        # Log
        self.log = []
        # Query events
        self.events["query_messages"] = self.query_messages
        self.events["query_data"] = self.query_data
        self.events["query_log"] = self.query_log

        self.events["set_working_directory"] = self.set_working_directory
        self.events["set_filename"] = self.set_filename
        self.events["start_record"] = self.start_record
        # Set the working directory
        self.working_dir = None
        self.filename = None

    def _process(self):
        self._recv()

    def exit(self, *args, **kwargs):
        print(self.log)
        self.close()

    def recv_message(self, s, **kwargs):
        self.messages.append((kwargs["source"], kwargs["timestamp"], s))

    def recv_log(self, timestamp, source, name, data):
        self.log.append((timestamp, source, name, data))

    def query_messages(self):
        self.zmq_sender.send(b"", zmq.SNDMORE)
        while len(self.messages):
            source, t, m = self.messages.pop(0)
            d = {"source": source,
                 "timestamp": t,
                 "message": m}
            self.zmq_sender.send(serialize_dict(d), zmq.SNDMORE)
        self.zmq_sender.send(b"")

    def query_data(self):
        return

    def query_log(self):
        return

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
