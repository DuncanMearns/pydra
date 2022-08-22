from PyQt5 import QtWidgets, QtCore

from ..layout import *
from ..state_machine import Stateful


class ExperimentButton(Stateful, QtWidgets.QPushButton):
    """Button in experiment control dock that starts and stops an experiment."""

    start_experiment = QtCore.pyqtSignal()  # emitted if button pressed in idle state
    interrupt = QtCore.pyqtSignal()  # emitted if button pressed in running state

    def __init__(self):
        super().__init__("START EXPERIMENT")
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPlay')))
        self.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
        self.start_experiment.connect(self.stateMachine.start_experiment)
        self.interrupt.connect(self.stateMachine.interrupt)

    def enterIdle(self):
        try:
            self.clicked.disconnect(self.interrupt)
        except TypeError:
            pass
        self.clicked.connect(self.start_experiment)
        self.setEnabled(True)
        self.setText("START EXPERIMENT")
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPlay')))

    def enterRunning(self):
        try:
            self.clicked.disconnect(self.start_experiment)
        except TypeError:
            pass
        self.clicked.connect(self.interrupt)
        self.setText("ABORT EXPERIMENT")
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaStop')))
