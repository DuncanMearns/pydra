from multiprocessing import Process, Queue, Event
import queue
import time
from collections import namedtuple, deque


WorkerConstructor = namedtuple('WorkerConstructor', ('type', 'args', 'kwargs'))


class _BaseProcess(Process):

    def __init__(self, constructor: WorkerConstructor, exit_flag: Event):
        super().__init__()
        self.constructor = constructor
        self.exit_flag = exit_flag

    def _make(self):
        self.worker = self.constructor.type(*self.constructor.args, **self.constructor.kwargs)

    def setup(self):
        self._make()
        self.worker.setup()

    def cleanup(self):
        self.worker.cleanup()

    def _process(self):
        return

    def run(self):
        self.setup()
        while not self.exit_flag.is_set():
            self._process()
        self.cleanup()


class AcquisitionProcess(_BaseProcess):

    def __init__(self, constructor: WorkerConstructor, exit_flag: Event, frame_queue: Queue):
        super().__init__(constructor, exit_flag)
        self.frame_queue = frame_queue

    def _process(self):
        frame_input = self.worker.acquire()
        self.frame_queue.put(frame_input)

    def cleanup(self):
        self.frame_queue.close()
        super().cleanup()


class TrackingProcess(_BaseProcess):

    def __init__(self, constructor: WorkerConstructor, exit_flag: Event,
                 frame_queue: Queue,
                 tracking_queue: Queue):
                 # display_queue: Queue):
        super().__init__(constructor, exit_flag)
        self.frame_queue = frame_queue
        self.tracking_queue = tracking_queue
        # self.display_queue = display_queue

    def _process(self):
        frame_input = self.frame_queue.get()
        tracked_frame = self.worker.process(*frame_input)
        self.tracking_queue.put(tracked_frame)
        # try:
        #     self.display_queue.put_nowait(TrackingOutput(*tracked_frame))
        # except queue.Full:
        #     pass

    def cleanup(self):
        self.tracking_queue.close()
        # self.display_queue.close()
        super().cleanup()


class SavingProcess(_BaseProcess):

    def __init__(self, constructor: WorkerConstructor, exit_flag: Event, tracking_queue: Queue):
        super().__init__(constructor, exit_flag)
        self.tracking_queue = tracking_queue

    def _process(self):
        tracked_frame = self.tracking_queue.get()
        self.worker.dump(*tracked_frame)
