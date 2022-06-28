from ..statemachine import Stateful
from PyQt5 import QtWidgets, QtCore


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
