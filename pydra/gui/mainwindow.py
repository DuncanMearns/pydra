from PyQt5 import QtWidgets, QtGui, QtCore
from pyqtgraph.dockarea import DockArea, Dock

from .dynamic import DynamicUpdate
from .state_machine import Stateful
from .images import icons
from .experiment_dock import *
from .pydra_interface import PydraInterface
from .public import *


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


class ExperimentWidget(QtWidgets.QWidget):

    def __init__(self, params: dict):
        super().__init__()
        self.setLayout(QtWidgets.QVBoxLayout())
        self.record_button = RecordButton()
        self.layout().addWidget(self.record_button)
        self.status_widget = StatusWidget()
        self.layout().addWidget(self.status_widget)
        self.file_naming_widget = FileNamingWidget(**params)
        self.layout().addWidget(self.file_naming_widget)
        self.trial_control_widget = TrialControlWidget(**params)
        self.layout().addWidget(self.trial_control_widget)
        self.protocol_widget = TrialStructureWidget(**params)
        self.layout().addWidget(self.protocol_widget)


class ControlDock(QtWidgets.QDockWidget):

    widgetEvent = QtCore.pyqtSignal(str, str, dict)

    def __init__(self, widget: ControlWidget, name: str, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.setWidget(widget)
        self.name = name
        self._set_widget_params()
        self._add_connections()

    def _set_widget_params(self):
        self.setMinimumWidth(250)
        self.setMinimumHeight(100)
        self.setMaximumHeight(350)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        self.setSizePolicy(size_policy)

    def _add_connections(self):
        # Show/hide
        self.displayAction = QtWidgets.QAction(self.name)
        self.displayAction.setCheckable(True)
        self.displayAction.setChecked(True)
        self.displayAction.triggered.connect(self.toggle_visibility)
        # Widget events
        self.widget().widgetEvent.connect(self.widgetEvent)

    @QtCore.pyqtSlot(bool)
    def toggle_visibility(self, state):
        if state:
            self.show()
        else:
            self.close()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.displayAction.setChecked(False)
        event.accept()


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
        # ============
        # Window title
        self.setWindowTitle("Pydra - Experiment Control")
        self.setWindowIcon(QtGui.QIcon(icons["python_logo"]))
        # =======
        # Menubar
        self.setMenuBar(QtWidgets.QMenuBar())
        self.windowMenu = self.menuWidget().addMenu("Window")
        # ===============
        params = pydra.config["gui_params"]
        # Experiment dock
        self.experiment_dock = QtWidgets.QDockWidget()
        self.experiment_widget = ExperimentWidget(params)
        self.experiment_dock.setWidget(self.experiment_widget)
        self.experiment_dock.setWindowTitle("Experiment control")
        self.experiment_dock.setFeatures(self.experiment_dock.DockWidgetMovable |
                                         self.experiment_dock.DockWidgetFloatable)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.experiment_dock)
        # =====================
        # Create display widget
        self.display_container = CentralWidget()
        self.setCentralWidget(self.display_container)
        # ================================
        # Add control widgets and plotters
        self.controllers = {}
        self._control_docks = {}
        self.plotters = {}
        for module in self.pydra.modules:
            name = module["worker"].name
            params = module.get("params", {})
            # self.caches[name] = WorkerCache(params.get("cachesize", 50000))
            if "controller" in module.keys():
                # Create control widget
                widget = module["controller"](name=name, params=params)
                self.add_controller(name, widget)
            if "plotter" in module.keys():
                # Create plotting widget
                plotter = module["plotter"](name=name, params=params)
                self.add_plotter(name, plotter)
        # ===============
        # Connect signals
        self.pydra.newData.connect(self.update_gui)
        # Propagate signals from control dock
        for name, dock_widget in self._control_docks.items():
            dock_widget.widgetEvent.connect(self.pydra.send_event)
        # =======================
        # Start the state machine
        self.stateMachine.start()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.pydra.exit()
        a0.accept()

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
