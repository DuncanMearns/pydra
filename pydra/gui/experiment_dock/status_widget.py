from PyQt5 import QtWidgets, QtCore
import time

from ..dynamic import Stateful


class StatusWidget(Stateful, QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        # Layout
        self.setLayout(QtWidgets.QGridLayout())
        self.layout().setAlignment(QtCore.Qt.AlignLeft)
        # Status
        self.layout().addWidget(QtWidgets.QLabel("Status:"), 0, 0)
        self.status_label = QtWidgets.QLabel("Idle")
        self.layout().addWidget(self.status_label, 0, 1)
        # Experiment time
        self.layout().addWidget(QtWidgets.QLabel("Experiment time:"), 1, 0)
        self.expt_t0 = 0
        self.expt_time_label = QtWidgets.QLabel(self.format_seconds(0))
        self.layout().addWidget(self.expt_time_label, 1, 1)
        # Trial
        self.layout().addWidget(QtWidgets.QLabel("Trial:"), 2, 0)
        # self.n_trials = 1
        # self.trial_number = 1
        self.trial_number_label = QtWidgets.QLabel("0/0")
        self.trial_status_label = QtWidgets.QLabel("Completed")
        self.layout().addWidget(self.trial_number_label, 2, 1)
        self.layout().addWidget(self.trial_status_label, 2, 2)
        # Trial time
        self.layout().addWidget(QtWidgets.QLabel("Trial time:"), 3, 0)
        self.trial_t0 = 0
        self.trial_time_label = QtWidgets.QLabel(self.format_seconds(0))
        self.layout().addWidget(self.trial_time_label, 3, 1)
        # Connections
        self.stateMachine.update_timer.timeout.connect(self.update_display)

    @staticmethod
    def format_seconds(s):
        h, s = divmod(s, 3600)
        m, s = divmod(s, 60)
        return f"{int(h):02d}:{int(m):02d}:{s:05.2f}"

    @property
    def expt_time(self):
        return self.format_seconds(time.perf_counter() - self.expt_t0)

    @property
    def trial_time(self):
        return self.format_seconds(time.perf_counter() - self.trial_t0)

    @QtCore.pyqtSlot()
    def update_display(self):
        if self.expt_t0:
            self.expt_time_label.setText(self.expt_time)
        if self.trial_t0:
            self.trial_time_label.setText(self.trial_time)

    def enterIdle(self):
        self.expt_t0 = 0
        self.status_label.setText("Idle")

    def enterRunning(self):
        self.status_label.setText("Running")
        self.expt_t0 = time.perf_counter()
        # self.trial_number = 1

    def startRecord(self):
        self.trial_t0 = time.perf_counter()
        self.trial_number_label.setText(f"{self.trial}/{self.n_trials}")

    def stopRecord(self):
        self.trial_t0 = 0
        # self.trial_number += 1
