from processes import *


FrameOutput = namedtuple('FrameOutput', ('frame_number', 'timestamp', 'frame'))


class MedusaNode:

    def __init__(self):
        super().__init__()

    def setup(self):
        return

    def cleanup(self):
        return


class CameraAcquisition(MedusaNode):

    def __init__(self, camera_type):
        super().__init__()
        self.camera_type = camera_type

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

    def __init__(self, grabber: WorkerConstructor, tracker: WorkerConstructor, saver: WorkerConstructor):
        self.grabber = grabber
        self.tracker = tracker
        self.saver = saver
        self.exit_flag = Event()
        self.frame_queue = Queue()
        self.tracking_queue = Queue()

    def start(self):

        self.acquisition_process = AcquisitionProcess(self.grabber, self.exit_flag, self.frame_queue)
        self.tracking_process = TrackingProcess(self.tracker, self.exit_flag, self.frame_queue, self.tracking_queue)
        self.saving_process = SavingProcess(self.saver, self.exit_flag, self.tracking_queue)

        self.acquisition_process.start()
        self.tracking_process.start()
        self.saving_process.start()

    def stop(self):

        self.exit_flag.set()

        self.acquisition_process.join()
        self.tracking_process.join()
        self.saving_process.join()

        print('All processes terminated.')
