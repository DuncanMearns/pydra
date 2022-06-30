from .control_widget import ControlWidget
from PyQt5 import QtWidgets, QtCore, QtGui


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
