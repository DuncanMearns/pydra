from .states import StateEnabled
from .plotter import Plotter
from PyQt5 import QtWidgets, QtGui, QtCore


class ModuleWidget(QtWidgets.QDockWidget, StateEnabled):

    plot = Plotter

    def __init__(self, name, parent, *args, **kwargs):
        super().__init__(name, parent)
        self.name = name
        # Set widget parameters
        self._set_widget_params()
        # Create plotter widget
        self.create_plotter(*args, **kwargs)
        # Add to parent window
        self._add_to_main()

    def create_plotter(self, *args, **kwargs):
        self.plotter = None
        if self.plot:
            self.plotter = self.plot(*args, **kwargs)

    def _set_widget_params(self):
        self.setMinimumWidth(250)
        self.setMinimumHeight(100)
        self.setMaximumHeight(300)

    def _add_to_main(self):
        # Add to dock
        self.parent().addDockWidget(QtCore.Qt.RightDockWidgetArea, self)
        # Add to window menu
        self.displayAction = QtWidgets.QAction(self.name, self.parent())
        self.displayAction.setCheckable(True)
        self.displayAction.setChecked(True)
        self.displayAction.triggered.connect(self.show_window)
        self.parent().windowMenu.addAction(self.displayAction)

    def show_window(self, state):
        if state:
            self.show()
        else:
            self.close()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.displayAction.setChecked(False)
        event.accept()

    def send_event(self, event_name, **kwargs):
        self.parent().pydra.send_event(event_name, target=self.name, **kwargs)

    def updatePlots(self, data, frame=None, **plotters):
        return


class DisplayProxy(ModuleWidget):

    def __init__(self, name, parent, *args, **kwargs):
        super().__init__(name, parent, *args, **kwargs)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        event.accept()

    def _add_to_main(self):
        self.close()
        return
