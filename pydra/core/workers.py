from .base import Worker
from collections import namedtuple, deque
from multiprocessing import Queue, Event
from multiprocessing.connection import Connection
import queue
import time


FrameOutput = namedtuple('FrameOutput', ('frame_number', 'timestamp', 'frame'))


class AcquisitionWorker(Worker):

    def __init__(self, q: Queue, **kwargs):
        """Generic worker for acquiring data from an input source (e.g. a camera or a file).

        Parameters
        ----------
        q : Queue
        """
        super().__init__(**kwargs)
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

    def __init__(self,
                 input_q: Queue,
                 output_queue: Queue,
                 gui_event: Event = None,
                 gui_conn: Connection = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.input_q = input_q
        self.output_q = output_queue
        self.gui = False
        if (gui_event is not None) and (gui_conn is not None):
            self.gui = True
            self.cache = deque(maxlen=5000)
            self.events.append((gui_event, self.send_to_gui))
            self.gui_conn = gui_conn

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
        for frame_input in self._flush(self.input_q):
            tracked_frame = self.track(*frame_input)
            self.output_q.put(tracked_frame)

    def send_to_gui(self):
        while len(self.cache):
            data = self.cache.popleft()
            self.gui_conn.send(data)
        self.gui_conn.send(None)


class SavingWorker(Worker):

    def __init__(self, q: Queue, **kwargs):
        super().__init__(**kwargs)
        self.q = q

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
        for data_from_queue in self._flush(self.q):
            self.dump(*data_from_queue)
        super().cleanup()


class MultiWorker(Worker):

    def __init__(self, workers: tuple, **kwargs):
        """Allows multiple worker classes to be run (sequentially) in the same core.

        Parameters
        ----------
        workers : tuple of tuples
            (MedusaWorker, worker_kwargs) pairs.
        kwargs
        """
        super().__init__(**kwargs)
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
