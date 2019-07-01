from .tracker_base import TrackerBase
from collections import deque


class Optogenetics(TrackerBase):

    def __init__(self, parent, laser_buffer, display_buffer):
        super().__init__(parent)
        self.laser_cache = deque(maxlen=laser_buffer)
        self.display_cache = deque(maxlen=display_buffer)

    def clear(self):
        """Method called when caches are cleared."""
        self.laser_cache.clear()
        self.display_cache.clear()

    def track(self, frame_number, timestamp, frame):
        """Method called when a new frame is available to track."""
        laser_status = self.parent.laser_on
        self.laser_cache.append(laser_status)
        self.display_cache.append(laser_status)

    def extend(self, frame_data):
        if len(frame_data) > 0:
            try:
                self.saving_flag = False
                laser_status = self.laser_cache.popleft()
                frame_data.append(laser_status)
            except IndexError:
                self.saving_flag = True
        else:
            self.saving_flag = True
