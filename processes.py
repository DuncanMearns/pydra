from multiprocessing import Process, Queue, Event
import queue
import time
from collections import namedtuple, deque


class _BaseProcess(Process):

    def __init__(self, worker_cls: type, exit_signal: Event, finished_signal: Event):
        super().__init__()
        self.worker_cls = worker_cls
        self.worker = None
        self.exit_signal = exit_signal
        self.finished_signal = finished_signal

    def _make(self):
        self.worker = self.worker_cls()

    def setup(self):
        self._make()
        self.worker.setup()

    def cleanup(self):
        self.worker.cleanup()

    def _process(self):
        return

    def _flush(self, q: Queue):
        while True:
            try:
                obj = q.get_nowait()
                yield obj
            except queue.Empty:
                return

    def run(self):
        self.setup()
        while not self.exit_signal.is_set():
            self._process()
        self.cleanup()
        self.finished_signal.set()


class AcquisitionProcess(_BaseProcess):

    def __init__(self,
                 worker_cls,
                 exit_signal: Event,
                 finished_signal: Event,
                 frame_queue: Queue):
        super().__init__(worker_cls, exit_signal, finished_signal)
        self.frame_queue = frame_queue

    def _process(self):
        frame_input = self.worker.acquire()
        self.frame_queue.put(frame_input)


class TrackingProcess(_BaseProcess):

    def __init__(self,
                 worker_cls,
                 exit_signal: Event,
                 finished_signal: Event,
                 frame_queue: Queue,
                 tracking_queue: Queue):
                 # display_queue: Queue):
        super().__init__(worker_cls, exit_signal, finished_signal)
        self.frame_queue = frame_queue
        self.tracking_queue = tracking_queue
        # self.display_queue = display_queue

    def _process(self):
        try:
            frame_input = self.frame_queue.get_nowait()
            tracked_frame = self.worker.process(*frame_input)
            self.tracking_queue.put(tracked_frame)
        except queue.Empty:
            time.sleep(0.001)
        # try:
        #     self.display_queue.put_nowait(TrackingOutput(*tracked_frame))
        # except queue.Full:
        #     pass

    def cleanup(self):
        for frame_input in self._flush(self.frame_queue):
            tracked_frame = self.worker.process(*frame_input)
            self.tracking_queue.put(tracked_frame)
        super().cleanup()


class SavingProcess(_BaseProcess):

    def __init__(self,
                 worker_cls,
                 exit_signal: Event,
                 finished_signal: Event,
                 tracking_queue: Queue):
        super().__init__(worker_cls, exit_signal, finished_signal)
        self.tracking_queue = tracking_queue

    def _process(self):
        try:
            tracked_frame = self.tracking_queue.get_nowait()
            self.worker.dump(*tracked_frame)
        except queue.Empty:
            time.sleep(0.001)

    def cleanup(self):
        for tracked_frame in self._flush(self.tracking_queue):
            self.worker.dump(*tracked_frame)
        super().cleanup()
