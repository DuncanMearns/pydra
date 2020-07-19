from pydra.pipeline import *

from pydra.acquisition import CameraAcquisition
from pydra.acquisition.cameras import PikeCamera

from pydra.gui.display import MainDisplayWidget
from pydra.gui.toolbar import LiveButton, RecordButton

from multiprocessing import Event, Pipe
from PyQt5 import QtCore, QtWidgets, QtGui
import sys


class PydraApp(QtWidgets.QMainWindow):

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

        # Acquisition
        self.acquisition = CameraAcquisition
        self.acquisition_kw = dict(camera_type=PikeCamera)

        # Tracking
        self.update_gui_event = Event()
        self.parent_conn, self.child_conn = Pipe(False)
        self.tracking = TrackingWorker
        self.tracking_kw = dict(gui_event=self.update_gui_event, gui_conn=self.child_conn)

        # Saving
        self.saving = SavingWorker
        self.saving_kw = dict()

        # =============================================
        # HANDLING OF "LIVE" AND "RECORD" STATE CHANGES
        # =============================================
        self._live = False
        self.changeLiveState.connect(self.toggle_live_state)
        self.changeRecordState.connect(self.toggle_record_state)
        self._live_state_attributes = [attr for attr in dir(self) if hasattr(getattr(self, attr), 'toggle_live')]
        self._record = False
        self._record_state_attributes = [attr for attr in dir(self) if hasattr(getattr(self, attr), 'toggle_record')]

    @QtCore.pyqtSlot()
    def toggle_live_state(self):
        self._live = not self._live
        for attr in self._live_state_attributes:
            getattr(self, attr).toggle_live(self._live)

    @QtCore.pyqtSlot()
    def toggle_record_state(self):
        self._record = not self._record
        for attr in self._record_state_attributes:
            getattr(self, attr).toggle_record(self._record)

    @QtCore.pyqtSlot(bool)
    def live_button_pressed(self, *args):
        if not self._live:
            self.start_pipeline()
        else:
            self.stop_pipeline()
        self.changeLiveState.emit()

    @QtCore.pyqtSlot(bool)
    def record_button_pressed(self, *args):
        if not self._record:
            self.start_pipeline()
        else:
            self.stop_pipeline()
        self.changeRecordState.emit()

    @QtCore.pyqtSlot()
    def start_pipeline(self):
        self.pipeline = PydraPipeline(self.acquisition, self.acquisition_kw,
                                      self.tracking, self.tracking_kw,
                                      self.saving, self.saving_kw)
        self.pipeline.start()
        self.timer.start(50)

    @QtCore.pyqtSlot()
    def stop_pipeline(self):
        self.pipeline.stop()
        self.timer.stop()

    @QtCore.pyqtSlot()
    def update_gui(self):
        self.update_gui_event.set()
        frames = []
        while True:
            data = self.parent_conn.recv()
            if data is None:
                break
            else:
                frames.append(data)
        if len(frames):
            frame = frames[-1].frame
            self.display.image.setImage(frame[::-1, :].T)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        if self._live or self._record:
            self.pipeline.stop()
            self.timer.stop()
        a0.accept()

    @staticmethod
    def run():
        app = QtWidgets.QApplication([])
        window = PydraApp()
        window.show()
        sys.exit(app.exec_())
