from PyQt5 import QtWidgets

from ..layout import *
from ..dynamic import Stateful


class RecordButton(Stateful, QtWidgets.QPushButton):

    def __init__(self):
        super().__init__("START EXPERIMENT")
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPlay')))
        self.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)

    def enterIdle(self):
        self.setEnabled(True)
        self.setText("START EXPERIMENT")
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPlay')))

    def enterRunning(self):
        self.setText("ABORT EXPERIMENT")
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaStop')))
