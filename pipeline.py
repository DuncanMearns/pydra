from processes import *
from vimba import PikeCamera

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
        self.grabber = grabber
        self.tracker = tracker
        self.saver = saver
        self.exit_signal = Event()
        self.finished_acquisition_signal = Event()
        self.finished_tracking_signal = Event()
        self.finished_saving_signal = Event()
        self.frame_queue = Queue()
        self.tracking_queue = Queue()

    @staticmethod
    def safe_start(process):
        process.start()
        if process.is_alive():
            return True
        else:
            return False

    def start(self):
        self.acquisition_process = AcquisitionProcess(self.grabber,
                                                      self.exit_signal,
                                                      self.finished_acquisition_signal,
                                                      self.frame_queue)
        self.tracking_process = TrackingProcess(self.tracker,
                                                self.finished_acquisition_signal,
                                                self.finished_tracking_signal,
                                                self.frame_queue,
                                                self.tracking_queue)
        self.saving_process = SavingProcess(self.saver,
                                            self.finished_tracking_signal,
                                            self.finished_saving_signal,
                                            self.tracking_queue)

        self.acquisition_process.start()
        self.tracking_process.start()
        self.saving_process.start()

    def stop(self):
        self.exit_signal.set()
        self.acquisition_process.join()
        self.tracking_process.join()
        self.saving_process.join()
        print('All processes terminated.')
