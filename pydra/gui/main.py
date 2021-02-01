from PyQt5 import QtCore, QtWidgets
from .toolbar import RecordingToolbar
from .plotting import PlotterWidget
from .states import StateEnabled
from .protocol import ProtocolWindow
from pydra.core.protocol import Protocol


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
        # Get the trigger object from pydra
        self.trigger = self.pydra.trigger

        # Set window title
        self.setWindowTitle("Pydra - Experiment Control")
        # Create the state machine
        self._create_state_machine()
        # ==========================

        # Create menubar
        self.setMenuBar(QtWidgets.QMenuBar())
        self.windowMenu = self.menuWidget().addMenu("Window")

        # Create a protocol object
        self.protocol = self.no_protocol()
        # Get worker events for building protocols
        self.worker_events = self.pydra.worker_events
        self.protocol_window = ProtocolWindow(self.worker_events, self)
        self.protocol_window.save_protocol.connect(self.addProtocol)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.protocol_window)

        # Add toolbar for recording
        self.recording_toolbar = RecordingToolbar(parent=self)
        self.addToolBar(self.recording_toolbar)
        self.idleState.addTransition(self.recording_toolbar.clicked, self.runningState)
        self.runningState.addTransition(self.recording_toolbar.clicked, self.idleState)
        self.runningState.entered.connect(self.run_protocol)
        self.runningState.exited.connect(self.end_protocol)

        # Create display widget
        self.displays = QtWidgets.QWidget()
        self.setCentralWidget(self.displays)

        # Add module widgets
        self.worker_widgets = {}
        for module in self.pydra.modules:
            if "widget" in module.keys():
                name = module["worker"].name
                self.worker_widgets[name] = module["widget"](name=name, parent=self)
        for name, widget in self.worker_widgets.items():
            self.addDockWidget(QtCore.Qt.RightDockWidgetArea, widget)

        # Create plotters
        self.plotter = PlotterWidget()
        self.setCentralWidget(self.plotter)
        for pipeline, workers in self.pydra.pipelines.items():
            params = []
            for worker in workers:
                params.extend([".".join([worker.name, param]) for param in worker.plot])
            self.plotter.addPlotter(pipeline, params)

        # Plotting update timer
        self.update_interval = 30
        self.update_timer = QtCore.QTimer()
        self.update_timer.setInterval(self.update_interval)
        self.update_timer.timeout.connect(self.update_plots)
        self.update_timer.start()

        # =======================
        # Start the state machine
        self._start_state_machine()

    def no_protocol(self):
        """Returns a free-running protocol."""
        protocol = Protocol("no protocol", 0, 0)
        if self.trigger:
            protocol.addTrigger(self.trigger)
        protocol.addEvent(self.pydra.start_recording)
        protocol.freeRunningMode()
        return protocol

    def build_protocol(self):
        """Creates a new protocol."""
        events = self.protocol_window.protocol
        n_reps, interval = self.recording_toolbar.protocol_widget.value
        if len(events):
            # Build protocol
            self.protocol = Protocol("protocol", n_reps, interval)
            if self.trigger:
                self.protocol.addTrigger(self.trigger)
            self.protocol.addEvent(self.pydra.start_recording)
            for event in events:
                if isinstance(event, str):
                    self.protocol.addEvent(self.pydra.send_event, event)
                elif isinstance(event, int):
                    self.protocol.addTimer(int(event * 1000))
            self.protocol.addEvent(self.pydra.stop_recording)
            self.runningState.addTransition(self.protocol.completed, self.idleState)
        else:
            self.protocol = self.no_protocol()
        self.protocol.started.connect(self.startRecord)
        self.protocol.finished.connect(self.endRecord)
        self.protocol.interrupted.connect(self.pydra.stop_recording)

    @QtCore.pyqtSlot(str, list)
    def addProtocol(self, name, protocol):
        """Adds a new protocol to pydra. NOT FULLY IMPLEMENTED."""
        self.pydra.protocols[name] = protocol

    @QtCore.pyqtSlot()
    def run_protocol(self):
        """Builds and runs a new protocol."""
        self.build_protocol()
        self.protocol()

    @QtCore.pyqtSlot()
    def end_protocol(self):
        """Ends the current protocol if interrupted before completion."""
        if self.protocol.running():
            self.protocol.interrupt()

    @QtCore.pyqtSlot()
    def update_plots(self):
        """Updates plots with data received from pydra."""
        for pipeline, data, frame in self.pydra.request_data():
            self.plotter.updatePlots(pipeline, data, frame)
