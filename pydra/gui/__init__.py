from PyQt5 import QtCore, QtWidgets, QtGui
from .startwindow import StartWindow
from .module import ControlWidget, PydraDockWidget
from .plotter import Plotter, DisplayContainer
from .toolbar import RecordingToolbar
from .states import Stateful
from .protocol import ProtocolWindow
from .cache import WorkerCache
from .images import icons
# from .connections import NetworkConfiguration
from pydra.utilities import clock


class MainWindow(Stateful, QtWidgets.QMainWindow):
    """Main window for Pydra application.

    Parameters
    ----------
    pydra :
        The Pydra instance.
    """

    def __init__(self, pydra, *args):
        super().__init__(*args)
        # Start pydra event loop
        self.pydra = pydra
        # ================
        # Set window title
        self.setWindowTitle("Pydra - Experiment Control")
        self.setWindowIcon(QtGui.QIcon(icons["python_logo"]))
        # ==============
        # Create menubar
        self.setMenuBar(QtWidgets.QMenuBar())
        self.windowMenu = self.menuWidget().addMenu("Window")
        # ======================
        # Create protocol window
        # self.worker_events = self.pydra.worker_events
        # self.protocol_window = ProtocolWindow(self.worker_events, self.pydra.protocols, parent=self)
        # self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.protocol_window)
        # =====================
        # Add recording toolbar
        self.recording_toolbar = RecordingToolbar(parent=self)
        self.addToolBar(self.recording_toolbar)
        # self.stateMachine.running.entered.connect(self.run_protocol)
        # self.runningState.exited.connect(self.pydra.end_protocol)
        # ==================
        # Create data caches
        self.caches = {}
        # =====================
        # Create display widget
        self.display_container = DisplayContainer()
        self.setCentralWidget(self.display_container)
        # Add control widgets and plotters
        self.controllers = {}
        self._control_docks = {}
        self.plotters = {}
        self._to_update = []
        for module in self.pydra.modules:
            name = module["worker"].name
            params = module.get("params", {})
            self.caches[name] = WorkerCache(params.get("cachesize", 50000))
            if "controller" in module.keys():
                # Create control widget
                widget = module["controller"](name=name, params=params)
                self.add_controller(name, widget)
            if "plotter" in module.keys():
                # Create plotting widget
                plotter = module["plotter"](name=name, params=params)
                self.add_plotter(name, plotter)
        # =================================
        # Send any missed events to widgets
        # for worker, log in self.pydra._event_log.items():
        #     for (t, event_name, event_kw) in log:
        #         self.controllers[worker].receiveLogged(event_name, event_kw)
        # =====================
        # Plotting update timer
        self.update_interval = 30
        self.update_timer = QtCore.QTimer()
        self.update_timer.setInterval(self.update_interval)
        self.update_timer.timeout.connect(self.update_plots)
        self.update_timer.start()

        # =======================
        # Start the state machine
        self.stateMachine.start()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.pydra.exit()
        a0.accept()

    def run_protocol(self):
        n_reps, interval = self.recording_toolbar.protocol_widget.value
        name = self.protocol_window.name
        if name:
            protocol = self.protocol_window.protocol
            self.pydra.build_protocol(name, n_reps, interval, protocol)
        else:
            self.pydra.freerunning_mode()
        self.recording_toolbar.protocol_widget.update_protocol(name)
        self.runningState.addTransition(self.pydra.protocol.completed, self.idleState)
        self.pydra.protocol.started.connect(self.startRecord)
        self.pydra.protocol.finished.connect(self.endRecord)
        self.pydra.run_protocol()

    def add_controller(self, name, widget):
        self.controllers[name] = widget
        # Check update enabled
        if widget.update_enabled:
            self._to_update.append((name, widget))
        # Create dock widget and add to main window
        dock_widget = PydraDockWidget(widget, name)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock_widget)
        self.windowMenu.addAction(dock_widget.displayAction)
        self._control_docks[name] = dock_widget

    def add_plotter(self, name, widget):
        self.plotters[name] = widget
        self.display_container.add(name, widget)
        self._to_update.append((name, widget))

    @QtCore.pyqtSlot()
    def update_plots(self):
        """Updates widgets with data received from pydra."""
        return
        # for worker, data, frame in self.pydra.request_data():
        #     self.caches[worker].update(clock.t0, data, frame)
        # for worker, widget in self._to_update:
        #     kw = dict([(w, cache) for (w, cache) in self.caches.items() if w != worker])
        #     widget.updatePlots(self.caches[worker], **kw)
        # # Check logged events
        # ret, log = self.pydra.request_events()
        # if ret:
        #     for (t, worker, event_name, event_kw) in log:
        #         self.controllers[worker].receiveLogged(event_name, event_kw)

    def enterRunning(self):
        self.pydra.start_recording()
    #     for worker, cache in self.caches.items():
    #         cache.clear()
    #     super().enterRunning()

    def enterIdle(self):
        self.pydra.stop_recording()
