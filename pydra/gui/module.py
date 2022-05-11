from .states import Stateful
from PyQt5 import QtWidgets, QtGui, QtCore


def disabled(method):
    return None


class ControlWidget(Stateful, QtWidgets.QWidget):

    sendEvent = QtCore.pyqtSignal(str, dict)

    def __init__(self, name, *args, **kwargs):
        super().__init__()
        self.name = name

    def send_event(self, event_name, **kwargs):
        self.sendEvent.emit(event_name, kwargs)

    @property
    def update_enabled(self):
        attr = getattr(self, "updatePlots", None)
        return callable(attr)

    @disabled
    def updatePlots(self, data_cache, **kwargs) -> None:
        return

    def receiveLogged(self, event_name, kw) -> None:
        return


class PydraDockWidget(Stateful, QtWidgets.QDockWidget):

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
        self.widget().sendEvent.connect(self.send_event)

    @QtCore.pyqtSlot(bool)
    def toggle_visibility(self, state):
        if state:
            self.show()
        else:
            self.close()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.displayAction.setChecked(False)
        event.accept()

    @QtCore.pyqtSlot(str, dict)
    def send_event(self, event_name, kwargs):
        self.parent().pydra.send_event(event_name, target=self.name, **kwargs)
