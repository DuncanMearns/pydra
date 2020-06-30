from processes import *
from vimba import PikeCamera
from collections import namedtuple, deque
import time
from multiprocessing import Event, Queue
import queue


FrameOutput = namedtuple('FrameOutput', ('frame_number', 'timestamp', 'frame'))


class AcquisitionWorker(MedusaWorker):

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


class CameraAcquisition(AcquisitionWorker):

    def __init__(self, q: Queue, camera_type: type, camera_kwargs: dict = None, **kwargs):
        super().__init__(q, **kwargs)
        self.camera_type = camera_type
        self.camera_kwargs = {}
        if camera_kwargs is not None:
            self.camera_kwargs.update(camera_kwargs)
        self.camera = None
        self.frame_number = 0

    def setup(self):
        self.camera = self.camera_type(**self.camera_kwargs)
        self.camera.open_camera()

    def acquire(self):
        frame = self.camera.read()
        timestamp = time.clock()
        output = FrameOutput(self.frame_number, timestamp, frame)
        self.frame_number += 1
        return output

    def cleanup(self):
        self.camera.release()


TrackingOutput = namedtuple('TrackingOutput', ('frame_number', 'timestamp', 'frame', 'data'))


class TrackingWorker(MedusaWorker):

    def __init__(self, input_q: Queue, output_queue: Queue, **kwargs):
        super().__init__(**kwargs)
        self.input_q = input_q
        self.output_q = output_queue

    def track(self, *args):
        """Analyse data from the input queue and return the result. Must be implemented in subclasses."""
        return args

    def _run(self):
        """Takes input from the input queue, runs track and puts the output in the output queue."""
        try:
            frame_input = self.input_q.get_nowait()
            tracked_frame = self.track(*frame_input)
            self.output_q.put(tracked_frame)
            # # TODO: DO NOT ADD EVERY FRAME! FILLS UP QUEUE!
            # self.gui_queue.put(tracked_frame.frame.copy())
        except queue.Empty:
            time.sleep(0.001)
        # try:
        #     self.display_queue.put_nowait(TrackingOutput(*tracked_frame))
        # except queue.Full:
        #     pass

    def cleanup(self):
        """Flushes the input queue."""
        for frame_input in self._flush(self.input_q):
            tracked_frame = self.track(*frame_input)
            self.output_q.put(tracked_frame)


class SavingWorker(MedusaWorker):

    def __init__(self, q: Queue, **kwargs):
        super().__init__(**kwargs)
        self.q = q

    def dump(self, *args):
        print(args[0])
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


class MultiWorker(MedusaWorker):

    def __init__(self, workers: tuple, **kwargs):
        """Allows multiple worker classes to be run (sequentially) in the same process.

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


class GuiQueue:

    def __init__(self, cache_size):
        super().__init__()
        self.queue = Queue()
        self.cache = deque(maxlen=cache_size)

    def _flush(self):
        while True:
            try:
                self.cache.append(self.queue.get_nowait())
            except queue.Empty:
                break

    def get(self):
        self._flush()
        try:
            return self.cache.pop()
        except IndexError:
            return

    def put(self, obj):
        self.queue.put(obj)


class MedusaPipeline:

    def __init__(self):
        """Handles multiprocessing of frame acquisition, tracking and saving.

        Parameters
        ----------
        grabber
            Acquisition class
        tracker
            Tracker class
        saver
            Saver class
        """
        # Signalling between processes
        self.exit_signal = Event()  # top-level exit signal for processes
        self.finished_acquisition_signal = Event()  # exit signal set when frame acquisition has ended
        self.finished_tracking_signal = Event()  # exit signal set when tracking has ended
        self.finished_saving_signal = Event()  # exit signal set when saving has ended
        # Queues
        self.frame_queue = Queue()  # queue filled by acquisition process and emptied by tracking process
        self.tracking_queue = Queue()  # queue filled by tracking process and emptied by saving process
        # self.gui_queue = GuiQueue(100)
        # Workers
        self.grabber = CameraAcquisition
        self.grabber_kwargs = dict(q=self.frame_queue, camera_type=PikeCamera)
        self.tracker = TrackingWorker
        self.tracker_kwargs = dict(input_q=self.frame_queue, output_queue=self.tracking_queue)
        self.saver = SavingWorker
        self.saver_kwargs = dict(q=self.tracking_queue)

    def start(self):
        # Initialise the acquisition process
        self.acquisition_process = MedusaProcess(self.grabber,
                                                 self.exit_signal,
                                                 self.finished_acquisition_signal,
                                                 self.grabber_kwargs)
        # Initialise the tracking process
        self.tracking_process = MedusaProcess(self.tracker,
                                              self.finished_acquisition_signal,
                                              self.finished_tracking_signal,
                                              self.tracker_kwargs)
        # Initialise the saving process
        self.saving_process = MedusaProcess(self.saver,
                                            self.finished_tracking_signal,
                                            self.finished_saving_signal,
                                            self.saver_kwargs)
        # Start all processes
        self.acquisition_process.start()
        self.tracking_process.start()
        self.saving_process.start()

    def stop(self):
        # Set the top-level exit signal telling the acquisition process to end
        self.exit_signal.set()
        # Join all processes
        self.acquisition_process.join()
        print('acquisition ended')
        # print(self.gui_queue.queue.qsize())
        self.tracking_process.join()
        print('tracking ended')
        self.saving_process.join()
        print('All processes terminated.')
