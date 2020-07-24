from collections import namedtuple, deque
from multiprocessing import Queue
from multiprocessing.connection import Connection
import queue
import time


class Worker:
    """
    Abstract worker class for Medusa core.

    Subclasses must implement a core method and may additionally implement a setup and cleanup method invoked at the
    beginning and end of the core run, respectively.
    """

    receive_events = False
    send_events = False

    def __init__(self, receiver: Connection = None, sender: Connection = None, **kwargs):
        self.events = {}
        self.receiver = receiver
        self.sender = sender

    @classmethod
    def make(cls, **kwargs):
        return WorkerConstructor(cls, **kwargs)

    def setup(self):
        """Method called once when a core is spawned."""
        return

    def _run(self):
        """Method that is called within a MedusaProcess's main loop until the exit signal has been set. Must be
        overwritten in subclasses."""
        return

    def _handle_events(self):
        if self.receive_events:
            events = []
            while self.receiver.poll():
                event_name, args = self.receiver.recv()
                events.append((event_name, args))
            for event_name, args in events:
                self.events[event_name](*args)

    def _flush_events(self):
        if self.receive_events:
            events = []
            while self.receiver.poll():
                event_name, args = self.receiver.recv()

    def cleanup(self):
        """Method called at the end of a core after the main loop has exited. After this method is called, the
        core's finished signal is set and the core ends."""
        return

    @staticmethod
    def _flush_queue(q: Queue):
        """Can be used to flush queues after an exit signal has been received."""
        while True:
            try:
                obj = q.get_nowait()
                yield obj
            except queue.Empty:
                return


class WorkerConstructor:

    def __init__(self, worker, **kwargs):
        self.worker = worker
        self.kwargs = kwargs

    def update(self, *args, **kwargs):
        for key, value in args:
            self.kwargs[key] = value
        self.kwargs.update(**kwargs)

    def __call__(self, *args, **kwargs):
        return self.worker(**self.kwargs)


FrameOutput = namedtuple('FrameOutput', ('frame_number', 'timestamp', 'frame'))


class AcquisitionWorker(Worker):

    def __init__(self, q: Queue, *args, **kwargs):
        """Generic worker for acquiring data from an input source (e.g. a camera or a file).

        Parameters
        ----------
        q : Queue
        """
        super().__init__(*args, **kwargs)
        self.queue = q

    def acquire(self):
        """Acquire data from a source. Called time _run is called. Must be implemented in subclasses."""
        return

    def _run(self):
        """Acquires some data and puts it in the frame queue."""
        data_input = self.acquire()
        self.queue.put(data_input)


TrackingOutput = namedtuple('TrackingOutput', ('frame_number', 'timestamp', 'frame', 'data'))


class TrackingWorker(Worker):

    receive_events = True
    send_events = True

    def __init__(self,
                 input_q: Queue,
                 output_queue: Queue,
                 gui: bool = False,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_q = input_q
        self.output_q = output_queue
        self.gui = gui
        if self.gui:
            self.cache = deque(maxlen=5000)
            self.events['send_to_gui'] = self.send_to_gui

    def track(self, *args):
        """Analyse data from the input queue and return the result. Must be implemented in subclasses."""
        return TrackingOutput(*args, None)

    def _run(self):
        """Takes input from the input queue, runs track and puts the output in the output queue."""
        try:
            frame_input = self.input_q.get_nowait()
            tracked_frame = self.track(*frame_input)
            self.output_q.put(tracked_frame)
            if self.gui:
                self.cache.append(TrackingOutput(*tracked_frame))
        except queue.Empty:
            time.sleep(0.001)

    def cleanup(self):
        """Flushes the input queue."""
        for frame_input in self._flush_queue(self.input_q):
            tracked_frame = self.track(*frame_input)
            self.output_q.put(tracked_frame)

    def send_to_gui(self):
        while len(self.cache):
            data = self.cache.popleft()
            self.sender.send(data)
        self.sender.send(None)


class SavingWorker(Worker):

    receive_events = True

    def __init__(self, q: Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events['save_to_metadata'] = self.save_to_metadata
        self.q = q
        self.metadata = {}

    def save_to_metadata(self, *args):
        return

    def dump(self, *args):
        """Dumping / saving method. Must be implemented in subclasses."""
        return

    def _run(self):
        """Takes input from a queue and dumps it somewhere."""
        try:
            data_from_queue = self.q.get_nowait()
            self.dump(*data_from_queue)
        except queue.Empty:
            time.sleep(0.001)

    def cleanup(self):
        """Flushes the queue"""
        for data_from_queue in self._flush_queue(self.q):
            self.dump(*data_from_queue)
        super().cleanup()


class ProtocolWorker(Worker):

    receive_events = True
    send_events = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MultiWorker(Worker):

    def __init__(self, workers: tuple, *args, **kwargs):
        """Allows multiple worker classes to be run (sequentially) in the same core.

        Parameters
        ----------
        workers : tuple of tuples
            (MedusaWorker, worker_kwargs) pairs.
        kwargs
        """
        super().__init__(*args, **kwargs)
        self.workers = []
        for worker, worker_kwargs in workers:
            kw = {}
            if worker_kwargs is not None:
                kw.update(worker_kwargs)
            self.workers.append(worker(**kw))

    def setup(self):
        for worker in self.workers:
            worker.setup()

    def _run(self):
        for worker in self.workers:
            worker._run()

    def cleanup(self):
        for worker in self.workers:
            worker.cleanup()
