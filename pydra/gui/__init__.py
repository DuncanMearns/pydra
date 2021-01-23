from .connections import NetworkConfiguration

from PyQt5 import QtCore, QtWidgets, QtGui, Qt
from .toolbar import RecordingToolbar
from .states import StateEnabled


class MainWindow(QtWidgets.QMainWindow, StateEnabled):

    def __init__(self, pydra, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Give app access to pydra
        self.pydra = pydra
        # Create the state machine
        self._create_state_machine()
        # ==========================

        # Add toolbar
        self.recording_toolbar = RecordingToolbar(parent=self)
        self.addToolBar(self.recording_toolbar)

        # =======================
        # Start the state machine
        self._start_state_machine()

    @QtCore.pyqtSlot()
    def setIdle(self):
        print("IDLE")
        super().setIdle()

    @QtCore.pyqtSlot()
    def setRecord(self):
        self.pydra.start_recording()
        super().setRecord()

    @QtCore.pyqtSlot()
    def endRecord(self):
        self.pydra.stop_recording()
        super().endRecord()
