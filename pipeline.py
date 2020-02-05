from processes import *
from vimba import PikeCamera
from collections import namedtuple


FrameOutput = namedtuple('FrameOutput', ('frame_number', 'timestamp', 'frame'))


class MedusaNode:

    def __init__(self):
        super().__init__()

    def setup(self):
        return

    def cleanup(self):
        return


class CameraAcquisition(MedusaNode):

    def __init__(self):
        super().__init__()
        self.camera_type = PikeCamera

    def setup(self):
        self.camera = self.camera_type()
        self.camera.open_camera()
        self.frame_number = 0

    def acquire(self):
        frame = self.camera.read()
        timestamp = time.clock()
        output = FrameOutput(self.frame_number, timestamp, frame)
        self.frame_number += 1
        return output

    def cleanup(self):
        self.camera.release()


TrackingOutput = namedtuple('TrackingOutput', ('frame_number', 'timestamp', 'frame', 'data'))


class Tracker(MedusaNode):

    def __init__(self):
        super().__init__()

    def process(self, frame_number, timestamp, frame):
        return TrackingOutput(frame_number, timestamp, frame, {})


class Saver(MedusaNode):

    def __init__(self):
        super().__init__()

    def dump(self, frame_number, timestamp, frame, data):
        print(frame_number)


# class DisplayQueue:
#
#     def __init__(self, cache_size):
#         super().__init__()
#         self.queue = Queue()
#         self.cache = deque(maxlen=cache_size)
#
#     def _flush(self):
#         while True:
#             try:
#                 self.cache.append(self.queue.get_nowait())
#             except queue.Empty:
#                 break
#
#     def get(self):
#         self._flush()
#         return self.cache.pop()
#
#     def put(self, obj):
#         self.queue.put(obj)


class MedusaPipeline:

    def __init__(self, grabber, tracker, saver):
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
        self.grabber = grabber
        self.tracker = tracker
        self.saver = saver
        # Signalling between processes
        self.exit_signal = Event()  # top-level exit signal for processes
        self.finished_acquisition_signal = Event()  # exit signal set when frame acquisition has ended
        self.finished_tracking_signal = Event()  # exit signal set when tracking has ended
        self.finished_saving_signal = Event()  # exit signal set when saving has ended
        # Queues
        self.frame_queue = Queue()  # queue filled by acquisition process and emptied by tracking process
        self.tracking_queue = Queue()  # queue filled by tracking process and emptied by saving process

    def start(self):
        # Initialise the acquisition process
        self.acquisition_process = AcquisitionProcess(self.grabber,
                                                      self.exit_signal,
                                                      self.finished_acquisition_signal,
                                                      self.frame_queue)
        # Initialise the tracking process
        self.tracking_process = TrackingProcess(self.tracker,
                                                self.finished_acquisition_signal,
                                                self.finished_tracking_signal,
                                                self.frame_queue,
                                                self.tracking_queue)
        # Initialise the saving process
        self.saving_process = SavingProcess(self.saver,
                                            self.finished_tracking_signal,
                                            self.finished_saving_signal,
                                            self.tracking_queue)
        # Start all processes
        self.acquisition_process.start()
        self.tracking_process.start()
        self.saving_process.start()

    def stop(self):
        # Set the top-level exit signal telling the acquisition process to end
        self.exit_signal.set()
        # Join all processes
        self.acquisition_process.join()
        self.tracking_process.join()
        self.saving_process.join()
        print('All processes terminated.')
