"""
Parallel processes for acquiring frames, tracking and saving output.
All processes inherit form the _BaseProcess class which contains the run method.
"""

from multiprocessing import Process, Queue, Event
import queue
import time


__all__ = ['AcquisitionProcess', 'TrackingProcess', 'SavingProcess']


class _BaseProcess(Process):

    def __init__(self, worker_cls: type, exit_signal: Event, finished_signal: Event):
        """Abstract base process with a setup, _process and cleanup method.

        Parameters
        ----------
        worker_cls : type
            Any class with a setup and cleanup method.
        exit_signal : Event
            Signal telling the main loop of the process when to exit.
        finished_signal : Event
            Signal sent by the process once it has finished.
        """
        super().__init__()
        self.worker_cls = worker_cls
        self.worker = None
        self.exit_signal = exit_signal
        self.finished_signal = finished_signal

    def _make(self):
        """Creates the worker for the process."""
        self.worker = self.worker_cls()

    def setup(self):
        """Called once when the process is started. Call to super required in subclass."""
        self._make()
        self.worker.setup()

    def cleanup(self):
        """Called once after the process has received an exit signal. Call to super required in subclass."""
        self.worker.cleanup()

    def process(self):
        """Called within the main loop of the process until it received the exit signal.
        Should be overwritten in subclass."""
        return

    @staticmethod
    def _flush(q: Queue):
        """Used to flush queues after the exit signal has been received."""
        while True:
            try:
                obj = q.get_nowait()
                yield obj
            except queue.Empty:
                return

    def run(self):
        """Code the runs when process is started."""
        self.setup()
        while not self.exit_signal.is_set():
            self.process()
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

    def process(self):
        """Acquires a frame from the worker and puts it in the frame queue."""
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

    def process(self):
        """Takes input from the frame queue, passes it to the worker's process method and puts the output in the
        tracking queue."""
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
        """Flushes the frame queue."""
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

    def process(self):
        """Takes input from the tracking queue and passes it to the worker's dump method."""
        try:
            tracked_frame = self.tracking_queue.get_nowait()
            self.worker.dump(*tracked_frame)
        except queue.Empty:
            time.sleep(0.001)

    def cleanup(self):
        """Flushes the tracking queue"""
        for tracked_frame in self._flush(self.tracking_queue):
            self.worker.dump(*tracked_frame)
        super().cleanup()
