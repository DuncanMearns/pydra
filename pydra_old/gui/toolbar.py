from .state import StateEnabled
from PyQt5 import QtWidgets


BUTTON_WIDTH = 100
BUTTON_HEIGHT = 50


class LiveButton(StateEnabled, QtWidgets.QPushButton):

    def __init__(self, width, height, *args, **kwargs):
        super().__init__("LIVE", *args, **kwargs)
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPlay')))
        self.setFixedSize(width, height)

    def idle(self):
        self.setEnabled(True)
        self.setText("LIVE")
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPlay')))

    def live(self):
        self.setText("STOP")
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPause')))

    def record(self):
        self.setEnabled(False)


class RecordButton(StateEnabled, QtWidgets.QPushButton):

    def __init__(self, width, height, *args, **kwargs):
        super().__init__("RECORD", *args, **kwargs)
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_DialogNoButton')))
        self.setFixedSize(width, height)

    def idle(self):
        self.setEnabled(True)
        self.setText("RECORD")
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_DialogNoButton')))

    def live(self):
        self.setEnabled(False)

    def record(self):
        self.setText("STOP")
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPause')))


class Toolbar(StateEnabled, QtWidgets.QToolBar):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFloatable(False)
        self.setMovable(False)
        # Live button
        self.live_button = LiveButton(BUTTON_WIDTH, BUTTON_HEIGHT)
        self.addWidget(self.live_button)
        # Record button
        self.record_button = RecordButton(BUTTON_WIDTH, BUTTON_HEIGHT)
        self.addWidget(self.record_button)

    def idle(self):
        self.live_button.idle()
        self.record_button.idle()

    def live(self):
        self.live_button.live()
        self.record_button.live()

    def record(self):
        self.live_button.record()
        self.record_button.record()
