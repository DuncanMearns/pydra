from ..pydra import Pydra

from .display import MainDisplayWidget
from .toolbar import LiveButton, RecordButton

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
        self.BUTTON_WIDTH = 100
        self.BUTTON_HEIGHT = 50

        # =======
        # TOOLBAR
        # =======
        self.TOOLBAR = self.addToolBar("toolbar")
        self.TOOLBAR.setFloatable(False)
        self.TOOLBAR.setMovable(False)
        # Live button
        self.LIVE_BUTTON = LiveButton(self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
        self.LIVE_BUTTON.clicked.connect(self.live_button_pressed)
        self.TOOLBAR.addWidget(self.LIVE_BUTTON)
        # Record button
        self.RECORD_BUTTON = RecordButton(self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
        self.RECORD_BUTTON.clicked.connect(self.record_button_pressed)
        self.TOOLBAR.addWidget(self.RECORD_BUTTON)

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

        # # Acquisition
        # self.acquisition = CameraAcquisition
        # self.acquisition_kw = dict(camera_type=PikeCamera)

        # Tracking
        # self.tracking = DummyTracker
        self.tracking_kw.update(gui=True)

        # # Saving
        # self.saving = VideoSaver
        # self.saving_kw = dict()

        # =============================================
        # HANDLING OF "LIVE" AND "RECORD" STATE CHANGES
        # =============================================
        self._live = False
        self._record = False
        self.changeLiveState.connect(self._toggle_live_state)
        self.changeRecordState.connect(self._toggle_record_state)

        self.start_pipeline()

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
        super().stop_pipeline()
        self.timer.stop()

    @QtCore.pyqtSlot()
    def update_gui(self):
        self.pipeline.tracking_event_sender.send(('send_to_gui', ()))
        frames = []
        while self.pipeline.tracking_event_receiver.poll():
            data = self.pipeline.receive_from_tracking.recv()
            if data is None:
                break
            else:
                frames.append(data)
        if len(frames):
            print(frames[0])
        #     frame = frames[-1].frame
        #     self.display.image.setImage(frame[::-1, :].T)

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
        if self._live or self._record:
            self.timer.stop()
        self.stop_pipeline()
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
