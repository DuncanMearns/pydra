from .connections import NetworkConfiguration

from PyQt5 import QtCore, QtWidgets, QtGui, Qt
from .toolbar import RecordingToolbar
from .pipeline import PlotterWidget
from .states import StateEnabled


class MainWindow(QtWidgets.QMainWindow, StateEnabled):

    def __init__(self, pydra, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Give app access to pydra
        self.pydra = pydra
        self.setWindowTitle("Pydra - Experiment Control")
        # Create the state machine
        self._create_state_machine()
        # ==========================

        # Create menubar
        self.setMenuBar(QtWidgets.QMenuBar())
        self.windowMenu = self.menuWidget().addMenu("Window")

        # Add toolbar
        self.recording_toolbar = RecordingToolbar(parent=self)
        self.addToolBar(self.recording_toolbar)

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

    def update_plots(self):
        for pipeline, data, frame in self.pydra.request_data():
            self.plotter.updatePlots(pipeline, data, frame)

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
