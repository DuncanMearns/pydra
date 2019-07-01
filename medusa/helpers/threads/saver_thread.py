from PyQt5 import QtCore
import numpy as np


class SaverThread(QtCore.QThread):
    """Python thread that saves helpers results from a cache"""

    def __init__(self, path, *args):
        super().__init__()
        self.path = path
        self.trackers = args
        self.exit_flag = False

    def run(self):
        tracking_data = []
        while (not self.exit_flag) or (not all([tracker.saving_flag for tracker in self.trackers])):
            frame_data = []
            for tracker in self.trackers:
                tracker.extend(frame_data)
            if len(frame_data) > 0:
                tracking_data.append(frame_data)
        tracking_data = np.array(tracking_data)
        np.save(self.path + '.npy', tracking_data)
        for tracker in self.trackers:
            tracker.dump()
