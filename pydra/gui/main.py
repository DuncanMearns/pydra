from PyQt5 import QtCore, QtWidgets, QtGui
from .toolbar import RecordingToolbar
from .display import DisplayContainer
from .states import StateEnabled
from .protocol import ProtocolWindow


class MainWindow(QtWidgets.QMainWindow, StateEnabled):
    """Main window for Pydra application.

    Parameters
    ----------
    pydra :
        The Pydra instance.
    """

    def __init__(self, pydra, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Give app access to pydra
        self.pydra = pydra

        # Set window title
        self.setWindowTitle("Pydra - Experiment Control")
        # Create the state machine
        self._create_state_machine()
        # ==========================

        # Create menubar
        self.setMenuBar(QtWidgets.QMenuBar())
        self.windowMenu = self.menuWidget().addMenu("Window")

        # Get worker events for building protocols
        self.worker_events = self.pydra.worker_events
        self.protocol_window = ProtocolWindow(self.worker_events, self.pydra.protocols, parent=self)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.protocol_window)

        # Add toolbar for recording
        self.recording_toolbar = RecordingToolbar(parent=self)
        self.addToolBar(self.recording_toolbar)
        self.idleState.addTransition(self.recording_toolbar.record, self.runningState)
        self.runningState.addTransition(self.recording_toolbar.record, self.idleState)
        self.runningState.entered.connect(self.run_protocol)
        self.runningState.exited.connect(self.pydra.end_protocol)

        # Create display widget
        self.display_container = DisplayContainer()
        self.setCentralWidget(self.display_container)

        # Add module widgets and displays
        self.worker_widgets = {}
        self.displays = {}
        for module in self.pydra.modules:
            name = module["worker"].name
            params = module.get("params", {})
            if "widget" in module.keys():
                # Create control widget
                widget = module["widget"](name=name, parent=self, params=params)
                self.worker_widgets[name] = widget
                # Create plotting widget
                if widget.plot:
                    plotter = widget.plotter
                    self.display_container.add(name, plotter)
                    self.displays[name] = plotter

        # Plotting update timer
        self.update_interval = 30
        self.update_timer = QtCore.QTimer()
        self.update_timer.setInterval(self.update_interval)
        self.update_timer.timeout.connect(self.update_plots)
        self.update_timer.start()

        # =======================
        # Start the state machine
        self._start_state_machine()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.pydra.shutdown()
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

    @QtCore.pyqtSlot()
    def update_plots(self):
        """Updates widgets with data received from pydra."""
        for worker, data, frame in self.pydra.request_data():
            if worker in self.worker_widgets:
                self.worker_widgets[worker].updatePlots(data, frame, **self.displays)
