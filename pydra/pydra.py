from .handler import Handler
from .cameras import PikeCamera
from .tracking import NoTracking
from .saving import VideoSaver
from .stimulation.optogenetics import Optogenetics
from .gui.display import MainDisplayWidget
from .gui.toolbar import Toolbar
from PyQt5 import QtCore, QtWidgets, QtGui
import sys


class Pydra:

    config = {
        'acquisition': PikeCamera,
        'tracking': NoTracking,
        'saving': VideoSaver,
        'protocol': Optogenetics
    }

    def __init__(self):
        self.acquisition = self.config['acquisition'](self)
        self.tracking = self.config['tracking'](self)
        self.saving = self.config['saving'](self)
        self.protocol = self.config['protocol'](self)

        self.handler = Handler(self.acquisition.to_tuple(),
                               self.tracking.to_tuple(),
                               self.saving.to_tuple(),
                               self.protocol.to_tuple())
        self._start_processes()

        # Set signals-slots to change worker parameters
        self.saving.paramsChanged.connect(self.handler.set_param)
        self.acquisition.paramsChanged.connect(self.handler.set_param)
        self.acquisition.paramsChanged.connect(self.saving.update_recording_params)

    def _start_processes(self):
        self.handler.start()

    def _join_processes(self):
        self.handler.exit()

    def start(self):
        self.handler.start_event_loop()
        # self.pipeline.protocol_sender.send(dict(stimulus_df=pd.DataFrame(dict(t=[0, 1, 2], stimulation=[0, 1, 0]))))
        # time.sleep(0.1)
        # self.handler.start_protocol_event_loop()

    def stop(self):
        self.handler.stop_event_loop()

    @staticmethod
    def app():
        app = QtWidgets.QApplication([])
        pydra = PydraApp()
        pydra.show()
        sys.exit(app.exec_())


class PydraApp(QtWidgets.QMainWindow, Pydra):

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
        self.idleState.entered.connect(self.idle)
        self.idleState.addTransition(self.toolbar.live_button.clicked, self.liveState)
        self.idleState.addTransition(self.toolbar.record_button.clicked, self.recordState)
        self.stateMachine.addState(self.idleState)
        # Live
        self.liveState.entered.connect(self.live)
        self.liveState.addTransition(self.toolbar.live_button.clicked, self.idleState)
        self.stateMachine.addState(self.liveState)
        # Record
        self.recordState.entered.connect(self.record)
        self.recordState.addTransition(self.toolbar.record_button.clicked, self.idleState)
        self.stateMachine.addState(self.recordState)

        # ============
        # DOCK WIDGETS
        # ============
        self.dock_widgets = {}
        self.dock_widgets[self.saving.name] = self.saving.widget(self.saving)
        self.dock_widgets[self.acquisition.name] = self.acquisition.widget(self.acquisition)
        for name, widget in self.dock_widgets.items():
            self.addDockWidget(QtCore.Qt.RightDockWidgetArea, widget)

        # ==================
        # SET INITIAL STATES
        # ==================
        # Set the tracking worker to be gui enabled
        self.handler.set_param(self.tracking.name, (('gui', True),))
        # Set initial state and start state machine
        self.stateMachine.setInitialState(self.idleState)
        self.stateMachine.start()

    @QtCore.pyqtSlot()
    def idle(self):
        if self.handler.startAcquisitionFlag.is_set():
            self.stop()
        self.toolbar.idle()
        for name, widget in self.dock_widgets.items():
            widget.idle()

    @QtCore.pyqtSlot()
    def live(self):
        self.handler.set_saving(False)
        self.toolbar.live()
        for name, widget in self.dock_widgets.items():
            widget.live()
        self.start()

    @QtCore.pyqtSlot()
    def record(self):
        self.handler.set_saving(True)
        self.toolbar.record()
        for name, widget in self.dock_widgets.items():
            widget.record()
        self.start()

    def start(self):
        super().start()
        self.timer.start(50)

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

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.timer.stop()
        self._join_processes()
        a0.accept()
