from ..dynamic import Stateful, DynamicUpdate
from PyQt5 import QtWidgets, QtCore


class ControlWidget(DynamicUpdate, Stateful, QtWidgets.QWidget):

    sendEvent = QtCore.pyqtSignal(str, dict)

    def __init__(self, name, *args, **kwargs):
        super().__init__()
        self.name = name

    def send_event(self, event_name, **kwargs):
        self.sendEvent.emit(event_name, kwargs)

    def receiveLogged(self, event_name, kw) -> None:
        return
