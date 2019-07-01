from .tracker_base import TrackerBase
from collections import deque
import cv2
import time


class _CameraBase(TrackerBase):

    def __init__(self, parent):
        super().__init__(parent)
        self.display_cache = deque(maxlen=self.parent.buffer_temp)
        self.timestamp_cache = deque(maxlen=self.parent.buffer_tracking)
        self.writer = None

    def clear(self):
        self.display_cache.clear()
        self.timestamp_cache.clear()

    def track(self, frame_number, timestamp, frame):
        self.parent.frame_output_cache.append((frame_number, timestamp, frame))
        self.display_cache.append(frame)
        self.timestamp_cache.append(timestamp)

    def extend(self, frame_data):
        try:
            self.saving_flag = False
            frame_number, timestamp, frame = self.parent.frame_output_cache.popleft()
            frame_data.extend([frame_number, timestamp])
            self.writer.write(frame)
        except IndexError:
            self.saving_flag = True
            time.sleep(0.02)

    def initialise_saving(self, path):
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.writer = cv2.VideoWriter(path + '.avi', fourcc, self.parent.frame_rate, self.parent.frame_size, False)
        return self.writer.isOpened()

    def cleanup_saving(self):
        self.writer.release()
