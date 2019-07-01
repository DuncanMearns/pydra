from PyQt5 import QtWidgets, QtCore


class SavingWindow(QtWidgets.QProgressDialog):

    def __init__(self, parent):
        super().__init__()

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
        dialog = SavingWindow(parent)
        dialog.exec_()
