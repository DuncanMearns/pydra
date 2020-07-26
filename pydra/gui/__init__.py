from ..pydra import Pydra

from .display import MainDisplayWidget
from .toolbar import Toolbar, LiveButton, RecordButton

from PyQt5 import QtCore, QtWidgets, QtGui
import sys


class PydraGUI(QtWidgets.QMainWindow, Pydra):

    changeLiveState = QtCore.pyqtSignal()
    changeRecordState = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ======
        # LAYOUT
        # ======
        self.setWindowTitle('Pydra Control Centre')
        # Window size
        self.WIDTH = 1000
        self.HEIGHT = 800
        self.resize(self.WIDTH, self.HEIGHT)
        # Button size


        # =======
        # TOOLBAR
        # =======
        self.toolbar = Toolbar()
        self.addToolBar(self.toolbar)

        # ======================
        # CENTRAL DISPLAY WIDGET
        # ======================
        self.display = MainDisplayWidget()
        self.setCentralWidget(self.display)

        # ====================================
        # ACQUISITION-TRACKING-SAVING PIPELINE
        # ====================================

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_gui)

        # ==========
        # GUI STATES
        # ==========
        self.stateMachine = QtCore.QStateMachine()
        self.idleState = QtCore.QState()
        self.liveState = QtCore.QState()
        self.recordState = QtCore.QState()
        # Idle
        self.idleState.entered.connect(self.set_idle_state)
        self.idleState.addTransition(self.toolbar.live_button.clicked, self.liveState)
        self.idleState.addTransition(self.toolbar.record_button.clicked, self.recordState)
        self.stateMachine.addState(self.idleState)
        # Live
        self.liveState.entered.connect(self.set_live_state)
        self.liveState.addTransition(self.toolbar.live_button.clicked, self.idleState)
        self.stateMachine.addState(self.liveState)
        # Record
        self.recordState.entered.connect(self.set_record_state)
        self.recordState.addTransition(self.toolbar.record_button.clicked, self.idleState)
        self.stateMachine.addState(self.recordState)
        # Set initial state and start state machine
        self.stateMachine.setInitialState(self.idleState)
        self.stateMachine.start()

        self.handler.set_param(self.tracking.name, (('gui', True),))

    @QtCore.pyqtSlot()
    def set_idle_state(self):
        self.toolbar.idle()

    @QtCore.pyqtSlot()
    def set_live_state(self):
        self.toolbar.live()

    @QtCore.pyqtSlot()
    def set_record_state(self):
        self.toolbar.record()

    @property
    def _live_state_attributes(self):
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, 'toggle_live'):
                yield attr

    @property
    def _record_state_attributes(self):
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, 'toggle_record'):
                yield attr

    @QtCore.pyqtSlot()
    def _toggle_live_state(self):
        self._live = not self._live
        for attr in self._live_state_attributes:
            attr.toggle_live(self._live)

    @QtCore.pyqtSlot()
    def _toggle_record_state(self):
        self._record = not self._record
        for attr in self._record_state_attributes:
            attr.toggle_record(self._record)

    @QtCore.pyqtSlot()
    def start(self):
        super().start()
        self.timer.start(50)

    @QtCore.pyqtSlot()
    def stop(self):
        self.timer.stop()
        super().stop()

    @QtCore.pyqtSlot()
    def update_gui(self):
        self.handler.send_event(self.tracking.name, 'send_to_gui', ())
        frames = []
        while True:
            ret, data = self.handler.receive_event(self.tracking.name)
            if ret:
                if data is None:
                    break
                else:
                    frames.append(data)
            else:
                break
        if len(frames):
            frame = frames[-1].frame
            self.display.image.setImage(frame[::-1, :].T)

    @QtCore.pyqtSlot(bool)
    def live_button_pressed(self, *args):
        if not self._live:
            self.start()
        else:
            self.stop()
        self.changeLiveState.emit()

    @QtCore.pyqtSlot(bool)
    def record_button_pressed(self, *args):
        if not self._record:
            self.start()
        else:
            self.stop()
        self.changeRecordState.emit()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.timer.stop()
        self._join_processes()
        a0.accept()

    @staticmethod
    def run():
        app = QtWidgets.QApplication([])
        pydra = PydraGUI()
        pydra.show()
        try:
            sys.exit(app.exec_())
        finally:
            pass
