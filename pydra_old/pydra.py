from .handler import Handler
from .cameras import PikeCamera
from .tracking.tail_tracker import TailTrackerPlugin
from .saving import VideoTrackingSaver
from .stimulation.optogenetics import Optogenetics
from .gui.display import MainDisplayWidget, MainPlotter
from .gui.toolbar import Toolbar
from PyQt5 import QtCore, QtWidgets, QtGui
from threading import Timer
import sys


class Pydra:

    config = {
        'acquisition': PikeCamera,
        'tracking': TailTrackerPlugin,
        'saving': VideoTrackingSaver,
        'protocol': Optogenetics
    }

    started = QtCore.pyqtSignal()
    stopped = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        # Create handler
        self.handler = Handler(self.config['acquisition'].to_tuple(),
                               self.config['tracking'].to_tuple(),
                               self.config['saving'].to_tuple(),
                               self.config['protocol'].to_tuple())

        # Initialize plugins
        self.acquisition = self.config['acquisition'](self)
        self.tracking = self.config['tracking'](self)
        self.saving = self.config['saving'](self)
        self.protocol = self.config['protocol'](self)

        # Start processes
        self.handler.start()

        # Set signals-slots to change worker parameters
        self.saving.paramsChanged.connect(self.handler.set_param)  # change saving params
        self.acquisition.paramsChanged.connect(self.handler.set_param)  # change acquisition params
        self.acquisition.paramsChanged.connect(self.saving.update_recording_params)  # pass on changes to saving
        self.tracking.paramsChanged.connect(self.handler.set_param)  # change tracking params

    def start(self):
        self.handler.start_event_loop()
        self.started.emit()

    def stop(self):
        self.handler.stop_event_loop()
        self.stopped.emit()

    def exit(self):
        self.handler.exit()

    @staticmethod
    def app():
        app = QtWidgets.QApplication([])
        pydra = PydraApp()
        pydra.show()
        sys.exit(app.exec_())


class PydraApp(QtWidgets.QMainWindow, Pydra):

    states = {'idle': 0,
              'live': 1,
              'record': 2}

    timeout = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ======
        # LAYOUT
        # ======
        self.setWindowTitle('Pydra Control Centre')
        # Window size
        self.WIDTH = 1500
        self.HEIGHT = 1000
        self.resize(self.WIDTH, self.HEIGHT)
        self.showMaximized()

        # =======
        # TOOLBAR
        # =======
        self.toolbar = Toolbar()
        self.addToolBar(self.toolbar)

        # ======================
        # CENTRAL DISPLAY WIDGET
        # ======================
        self.display = MainDisplayWidget(parent=self)
        self.setCentralWidget(self.display)
        self.plotters = [MainPlotter.add(self.display, "main")]

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
        self.recordState.addTransition(self.timeout, self.idleState)
        self.stateMachine.addState(self.recordState)

        # =======
        # PLUGINS
        # =======
        self.dock_widgets = {}
        for plugin in (self.saving, self.acquisition, self.tracking, self.protocol):
            if plugin.widget is not None:
                widget = plugin.widget(plugin)
                self.dock_widgets[plugin.name] = widget
                self.addDockWidget(QtCore.Qt.RightDockWidgetArea, widget)
            if plugin.plotter is not None:
                self.plotters.append(plugin.plotter.add(self.display, plugin.name))

        # ==================
        # SET INITIAL STATES
        # ==================
        # Set the tracking worker to be gui enabled
        self.handler.set_param(self.tracking.name, (('gui', True),))
        # Set initial state and start state machine
        self.currentState = self.states['idle']
        self.stateMachine.setInitialState(self.idleState)
        self.stateMachine.start()

        # =========
        # Recording
        # =========
        self.recordTime = 0
        self.recordTimer = Timer(0, lambda x: x)  # initialize with dummy timer

    @QtCore.pyqtSlot()
    def idle(self):
        self.currentState = self.states['idle']
        if self.handler.startAcquisitionFlag.is_set():
            self.stop()
        self.toolbar.idle()
        for name, widget in self.dock_widgets.items():
            widget.enterIdle()

    @QtCore.pyqtSlot()
    def live(self):
        self.currentState = self.states['live']
        self.handler.set_saving(False)
        self.toolbar.live()
        for name, widget in self.dock_widgets.items():
            widget.live()
        self.start()

    @QtCore.pyqtSlot()
    def record(self):
        self.currentState = self.states['record']
        self.handler.set_saving(True)
        self.toolbar.record()
        for name, widget in self.dock_widgets.items():
            widget.enterRunning()
        self.start()

    def start(self):
        for plotter in self.plotters:
            plotter.reset()
        super().start()
        if (self.currentState == self.states['record']) and self.recordTime:
            self.recordTimer = Timer(self.recordTime, lambda: self.timeout.emit())
            self.recordTimer.start()
        self.timer.start(50)

    def stop(self):
        self.timer.stop()
        self.recordTimer.cancel()
        super().stop()

    @QtCore.pyqtSlot()
    def update_gui(self):
        # Receive new tracking data
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
        # Receive new protocol data
        kw = {'protocol_data': []}
        if self.handler.startProtocolFlag.is_set():
            while True:
                ret, protocol_data = self.handler.receive_event(self.protocol.name)
                if ret:
                    kw['protocol_data'].append(protocol_data)
                else:
                    break
        if len(frames):
            for plotter in self.plotters:
                plotter.update(*frames, **kw)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.timer.stop()
        self.exit()
        a0.accept()
