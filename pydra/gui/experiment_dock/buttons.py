from PyQt5 import QtWidgets, QtCore

from ..layout import *
from ..dynamic import Stateful


class RecordButton(Stateful, QtWidgets.QPushButton):

    start_experiment = QtCore.pyqtSignal()
    interrupt = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__("START EXPERIMENT")
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPlay')))
        self.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)

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
