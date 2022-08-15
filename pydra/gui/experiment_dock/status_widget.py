from PyQt5 import QtWidgets, QtCore
import time

from ..state_machine import Stateful


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
        self.expt_time_label = QtWidgets.QLabel(self.format_seconds(0))
        self.layout().addWidget(self.expt_time_label, 1, 1)
        # Trial
        self.layout().addWidget(QtWidgets.QLabel("Trial:"), 2, 0)
        self.trial_number_label = QtWidgets.QLabel("0/0")
        self.trial_status_label = QtWidgets.QLabel("")
        self.layout().addWidget(self.trial_number_label, 2, 1)
        self.layout().addWidget(self.trial_status_label, 2, 2)
        # Trial time
        self.trial_status_label = QtWidgets.QLabel("Trial time:")
        self.trial_time_label = QtWidgets.QLabel(self.format_seconds(0))
        self.layout().addWidget(self.trial_status_label, 3, 0)
        self.layout().addWidget(self.trial_time_label, 3, 1)
        # Connections
        self.stateMachine.update_timer.timeout.connect(self.update_time)
        self.stateMachine.n_trials_changed.connect(self.update_trial_number_label)
        self.stateMachine.trial_index_changed.connect(self.update_trial_number_label)

    @staticmethod
    def format_seconds(s):
        h, s = divmod(s, 3600)
        m, s = divmod(s, 60)
        return f"{int(h):02d}:{int(m):02d}:{s:05.2f}"

    @property
    def expt_time(self):
        return self.format_seconds(self.timers["experiment"].time)

    @property
    def trial_time(self):
        return self.format_seconds(self.timers["trial"].time)

    @property
    def wait_time(self):
        return self.format_seconds(self.timers["wait"].time)

    @QtCore.pyqtSlot()
    def update_time(self):
        if self.is_running():
            self.expt_time_label.setText(self.expt_time)
        if self.is_recording():
            self.trial_time_label.setText(self.trial_time)
        if self.is_waiting():
            self.trial_time_label.setText(self.wait_time)

    @QtCore.pyqtSlot(int)
    def update_trial_number_label(self, val):
        self.trial_number_label.setText(f"{self.trial_index}/{self.n_trials}")

    def enterIdle(self):
        self.status_label.setText("Idle")

    def enterRunning(self):
        self.status_label.setText("Running")

    def startRecord(self):
        self.trial_status_label.setText("Trial time:")

    def startWait(self):
        self.trial_status_label.setText("Waiting:")
