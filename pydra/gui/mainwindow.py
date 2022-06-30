from pydra.protocol import build_protocol
from .dynamic import Stateful, DynamicUpdate
from .cache import WorkerCache
from .images import icons
from .experiment_dock import ExperimentWidget
from .control_dock import ControlDock
# from .connections import NetworkConfiguration

from PyQt5 import QtWidgets, QtGui, QtCore
from pyqtgraph.dockarea import DockArea, Dock
import os


def connect_signal(method, signal):
    def wrapper(*args, **kwargs):
        result = method(*args, **kwargs)
        signal.emit(result)
        return result
    return wrapper


class PydraInterface(Stateful, QtCore.QObject):

    newData = QtCore.pyqtSignal(dict)

    def __init__(self, pydra):
        super().__init__()
        # Pydra
        self.pydra = pydra
        self.protocol = None
        # Wrap pydra methods
        self.pydra.receive_data = connect_signal(self.pydra.receive_data, self.newData)
        # Trial
        self.directory = self.config.get("default_directory", os.getcwd())
        self.filename = self.config.get("default_filename", "")
        self.trial_index = 0

    def __getattr__(self, item):
        return getattr(self.pydra, item)

    @QtCore.pyqtSlot()
    def fetch_messages(self):
        """Polls pydra for new data and dispatches requests."""
        self.pydra.poll()
        self.pydra.send_request("data")

    @QtCore.pyqtSlot(str)
    def set_filename(self, fname):
        print(fname)

    @QtCore.pyqtSlot(str)
    def set_directory(self, directory):
        print(directory)

    @QtCore.pyqtSlot(int)
    def set_trial_number(self, idx):
        print(idx)

    @QtCore.pyqtSlot(int)
    def set_n_trials(self, n):
        print(n)

    @QtCore.pyqtSlot(int)
    def set_inter_trial_interval(self, ms):
        print(ms)

    @QtCore.pyqtSlot(list)
    def set_protocol(self, event_list):
        print(event_list)

    @QtCore.pyqtSlot(str, str, dict)
    def send_event(self, target, event_name, event_kw):
        self.pydra.send_event(event_name, target=target, **event_kw)

    def enterIdle(self):
        """Broadcasts a start_recording event."""
        self.pydra.send_event("stop_recording")

    def enterRunning(self):
        """Broadcasts a start_recording event."""
        directory = str(self.directory)
        filename = str(self.filename)
        idx = int(self.trial_index)
        self.pydra.send_event("start_recording", directory=directory, filename=filename, idx=idx)


class CentralWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLayout(QtWidgets.QVBoxLayout())
        self._dock_area = DockArea()
        self.layout().addWidget(self._dock_area)

    def add(self, name: str, widget) -> None:
        dock = Dock(name)
        dock.addWidget(widget)
        self._dock_area.addDock(dock)


class MainWindow(Stateful, QtWidgets.QMainWindow):
    """Main window for Pydra application.

    Parameters
    ----------
    pydra :
        The Pydra instance.
    """

    def __init__(self, pydra, *args):
        super().__init__(*args)
        self.pydra = PydraInterface(pydra)
        # ================
        # Window title
        self.setWindowTitle("Pydra - Experiment Control")
        self.setWindowIcon(QtGui.QIcon(icons["python_logo"]))
        # ==============
        # Menubar
        self.setMenuBar(QtWidgets.QMenuBar())
        self.windowMenu = self.menuWidget().addMenu("Window")
        # ======================
        # Experiment dock
        # self.worker_events = self.pydra.worker_events
        self.experiment_dock = QtWidgets.QDockWidget()
        self.experiment_widget = ExperimentWidget()
        self.experiment_dock.setWidget(self.experiment_widget)
        self.experiment_dock.setWindowTitle("Experiment control")
        self.experiment_dock.setFeatures(self.experiment_dock.DockWidgetMovable |
                                         self.experiment_dock.DockWidgetFloatable)
        # self.experiment_dock.setMinimumWidth(250)
        # self.experiment_dock.setMinimumHeight(100)
        # size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        # self.experiment_dock.setSizePolicy(size_policy)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.experiment_dock)
        # =====================
        # Add recording toolbar
        # self.recording_toolbar = RecordingToolbar(parent=self)
        # self.addToolBar(self.recording_toolbar)
        # self.stateMachine.running.entered.connect(self.run_protocol)
        # self.runningState.exited.connect(self.pydra.end_protocol)
        # ==================
        # Create data caches
        self.caches = {}
        # =====================
        # Create display widget
        self.display_container = CentralWidget()
        self.setCentralWidget(self.display_container)
        # Add control widgets and plotters
        self.controllers = {}
        self._control_docks = {}
        self.plotters = {}
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
        # ===============
        # Connect signals
        self.pydra.newData.connect(self.update_gui)
        # Propagate signals from experiment dock
        self.experiment_widget.directory_changed.connect(self.pydra.set_directory)
        self.experiment_widget.filename_changed.connect(self.pydra.set_filename)
        self.experiment_widget.trial_number_changed.connect(self.pydra.set_trial_number)
        self.experiment_widget.n_trials_changed.connect(self.pydra.set_n_trials)
        self.experiment_widget.inter_trial_interval_changed.connect(self.pydra.set_inter_trial_interval)
        self.experiment_widget.protocol_changed.connect(self.pydra.set_protocol)
        # Propagate signals from control dock
        for name, dock_widget in self._control_docks.items():
            dock_widget.widgetEvent.connect(self.pydra.send_event)
        # =====================
        # Plotting update timer
        self.update_interval = 30
        self.update_timer = QtCore.QTimer()
        self.update_timer.setInterval(self.update_interval)
        self.update_timer.timeout.connect(self.pydra.fetch_messages)
        self.update_timer.start()
        # =======================
        # Start the state machine
        self.stateMachine.start()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.pydra.exit()
        a0.accept()

    # def run_protocol(self):
    #     n_reps, interval = self.recording_toolbar.protocol_widget.value
    #     name = self.protocol_window.name
    #     if name:
    #         protocol = self.protocol_window.protocol
    #         self.pydra.build_protocol(name, n_reps, interval, protocol)
    #     else:
    #         self.pydra.freerunning_mode()
    #     self.recording_toolbar.protocol_widget.update_protocol(name)
    #     self.runningState.addTransition(self.pydra.protocol.completed, self.idleState)
    #     self.pydra.protocol.started.connect(self.startRecord)
    #     self.pydra.protocol.finished.connect(self.endRecord)
    #     self.pydra.run_protocol()

    def add_controller(self, name, widget):
        self.controllers[name] = widget
        # Create dock widget and add to main window
        dock_widget = ControlDock(widget, name)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock_widget)
        self.windowMenu.addAction(dock_widget.displayAction)
        self._control_docks[name] = dock_widget

    def add_plotter(self, name, widget):
        self.plotters[name] = widget
        self.display_container.add(name, widget)

    @QtCore.pyqtSlot(dict)
    def update_gui(self, data):
        """Updates widgets with data received from pydra."""
        to_update = []
        for worker, new_data in data.items():
            for widget in [self.plotters.get(worker, None), self.controllers.get(worker, None)]:
                if isinstance(widget, DynamicUpdate):
                    widget.cache.update(new_data)
                    to_update.append(widget)
        for widget in to_update:
            widget.dynamicUpdate()

    # def enterRunning(self):
    #     self.pydra.start_recording()
    # #     for worker, cache in self.caches.items():
    # #         cache.clear()
    # #     super().enterRunning()
    #
    # def enterIdle(self):
    #     self.pydra.stop_recording()
