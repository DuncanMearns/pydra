from .state import LiveStateMixin, RecordStateMixin
from PyQt5 import QtWidgets


class QToggleButton(LiveStateMixin, RecordStateMixin, QtWidgets.QPushButton):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class LiveButton(QToggleButton):

    def __init__(self, width, height, *args, **kwargs):
        super().__init__("LIVE", *args, **kwargs)
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPlay')))
        self.setFixedSize(width, height)

    def toggle_live(self, state):
        if state:
            self.setText("STOP")
            self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPause')))
        else:
            self.setText("LIVE")
            self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPlay')))

    def toggle_record(self, state):
        if state:
            self.setEnabled(False)
        else:
            self.setEnabled(True)


class RecordButton(QToggleButton):

    def __init__(self, width, height, *args, **kwargs):
        super().__init__("RECORD", *args, **kwargs)
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_DialogNoButton')))
        self.setFixedSize(width, height)

    def toggle_live(self, state):
        if state:
            self.setEnabled(False)
        else:
            self.setEnabled(True)

    def toggle_record(self, state):
        if state:
            self.setText("STOP")
            self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPause')))
        else:
            self.setText("RECORD")
            self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_DialogNoButton')))
