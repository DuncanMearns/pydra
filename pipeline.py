from processes import *
from vimba import PikeCamera
from collections import namedtuple, deque
import time
from multiprocessing import Event, Queue
from multiprocessing.connection import Connection
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
        return args

    def _run(self):
        """Takes input from the input queue, runs track and puts the output in the output queue."""
        try:
            frame_input = self.input_q.get_nowait()
            tracked_frame = self.track(*frame_input)
            self.output_q.put(tracked_frame)
            if self.gui:
                self.cache.append(FrameOutput(*tracked_frame))
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


class MedusaPipeline:

    def __init__(self, event, conn):
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
        # Workers
        self.grabber = CameraAcquisition
        self.grabber_kwargs = dict(q=self.frame_queue, camera_type=PikeCamera)
        self.tracker = TrackingWorker
        self.tracker_kwargs = dict(input_q=self.frame_queue, output_queue=self.tracking_queue, gui_event=event, gui_conn=conn)
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
