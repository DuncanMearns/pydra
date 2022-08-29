from PyQt5 import QtWidgets, QtGui, QtCore
from pyqtgraph.dockarea import DockArea, Dock

from .dynamic import DynamicUpdate
from .state_machine import Stateful
from .images import icons
from .experiment_dock import *
from .pydra_interface import PydraInterface
from .public import *


class CentralWidget(QtWidgets.QWidget):
    """Simple widget class that acts as the central widget in the main window. Contains space for docking user-defined
    Plotter widgets."""

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
    """The widget that goes into the experiment control dock. Contains widgets/button/fields for starting and stopping
    an experiment, file naming, trial structure, defining protocols etc."""

    def __init__(self, params: dict):
        super().__init__()
        self.setLayout(QtWidgets.QVBoxLayout())
        self.experiment_button = ExperimentButton()
        self.layout().addWidget(self.experiment_button)
        self.status_widget = StatusWidget()
        self.layout().addWidget(self.status_widget)
        self.file_naming_widget = FileNamingWidget(**params)
        self.layout().addWidget(self.file_naming_widget)
        self.trial_control_widget = TrialControlWidget(**params)
        self.layout().addWidget(self.trial_control_widget)
        self.triggers_widget = TriggersWidget(**params)
        self.layout().addWidget(self.triggers_widget)
        self.protocol_widget = TrialStructureWidget(**params)
        self.layout().addWidget(self.protocol_widget)


class ControlDock(QtWidgets.QDockWidget):
    """Allows user-defined ControlWidgets to be dockable."""

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

    Attributes
    ----------
    pydra : PydraInterface
        The PydraInterface instance. Allows GUI to interface more easily with Pydra using signals and slots.
    experiment_widget : ExperimentWidget
        The instance of the dockable widget containing experiment/trial structure/protocol settings etc.
    display_container : CentralWidget
        The central widget of the GUI. Contains user-defined plotters.
    controllers : dict
        A dictionary of user-defined ControlWidget widgets.
    plotters : dict
        A dictionary of user-defined Plotter widgets.
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
        # Get gui params from config
        params = self.pydra.config["gui_params"]
        # Add event names to params
        params["event_names"] = self.event_names
        params["targets"] = self.workers
        # Add triggers to params
        params["triggers"] = self.pydra.triggers.threads
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
            name = module.name
            params = module.params
            if module.widget:
                # Create control widget
                widget = module.widget(name=name, params=params)
                self.add_controller(name, widget)
            if module.plotter:
                # Create plotting widget
                plotter = module.plotter(name=name, params=params)
                self.add_plotter(name, plotter)
        # ===============
        # Connect signals
        self.pydra.update_gui.connect(self.update_gui)
        # Propagate signals from control dock
        for name, dock_widget in self._control_docks.items():
            dock_widget.widgetEvent.connect(self.pydra.send_event)
        # =======================
        # Start the state machine
        self.stateMachine.start()
        self.last_t = 0

    @property
    def workers(self) -> tuple:
        """Property for accessing all workers in Pydra config."""
        workers = []
        for module in self.pydra.config["modules"]:
            workers.append(module["worker"].name)
        return tuple(workers)

    @property
    def event_names(self) -> tuple:
        """Property for accessing all defined gui_events from Pydra workers."""
        events = []
        for module in self.pydra.config["modules"]:
            gui_events = module["worker"].gui_events
            events.extend(gui_events)
        return tuple({event for event in events})

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.pydra.exit()
        a0.accept()

    def add_controller(self, name, widget):
        """Add a ControlWidget to the window.

        Parameters
        ----------
        name : str
            Associated worker name.
        widget : Plotter
            A user-defined ControlWidget.
        """
        self.controllers[name] = widget
        # Create dock widget and add to main window
        dock_widget = ControlDock(widget, name)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock_widget)
        self.windowMenu.addAction(dock_widget.displayAction)
        self._control_docks[name] = dock_widget

    def add_plotter(self, name, widget):
        """Add a plotter to the window.

        Parameters
        ----------
        name : str
            Associated worker name.
        widget : Plotter
            A user-defined Plotter widget.
        """
        self.plotters[name] = widget
        self.display_container.add(name, widget)

    @QtCore.pyqtSlot(dict)
    def update_gui(self, data):
        """Updates widgets with data received from Pydra."""
        to_update = []
        for worker, new_data in data.items():
            for widget in [self.plotters.get(worker, None), self.controllers.get(worker, None)]:
                if isinstance(widget, DynamicUpdate):
                    widget.cache.update(new_data)
                    to_update.append(widget)
        for widget in set(to_update):
            widget.dynamicUpdate()
