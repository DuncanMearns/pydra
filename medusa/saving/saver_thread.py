from PyQt5 import QtCore, QtWidgets
import time


class SaveProgressWindow(QtWidgets.QProgressDialog):

    def __init__(self, parent):
        super(SaveProgressWindow, self).__init__()

        self.setModal(True)
        self.setWindowTitle('Saving')

        self.parent = parent
        self.frames_to_save = float(len(self.parent.frame_cache_output) + 1)

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.check_progress)
        self.timer.start()

    def check_progress(self):
        n = len(self.parent.frame_cache_output)
        if n == 0:
            self.close()
        percent = 100 * (1 + self.frames_to_save - n) / self.frames_to_save
        self.setValue(percent)

    @staticmethod
    def run(parent):
        dialog = SaveProgressWindow(parent)
        dialog.exec_()


class SaverThread(QtCore.QThread):
    """Python thread that saves tracking results from a cache"""

    def __init__(self, saver, writer, frame_cache, *args, **kwargs):
        super(SaverThread, self).__init__()
        self.saver = saver(*args, **kwargs)
        self.writer = writer
        self.frame_cache = frame_cache
        self.exit_flag = False

    def run(self):
        while not(self.exit_flag) or (len(self.frame_cache) > 0):
            try:
                frame_number, timestamp, laser_status, img = self.frame_cache.popleft()
                self.writer.write(img)
                self.saver.append(frame_number, timestamp, laser_status)
            except IndexError:
                time.sleep(0.02)
        self.saver.dump()
