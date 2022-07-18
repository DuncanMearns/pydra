from PyQt5 import QtCore
from ..protocol import events
import typing


class QProtocolEvent(QtCore.QObject):

    finished = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

    def start(self):
        pass

    @QtCore.pyqtSlot()
    def interrupt(self):
        pass

    @QtCore.pyqtSlot()
    def interrupt(self):
        self.finished.emit()


class QPause(QProtocolEvent):

    def __init__(self, msec):
        super().__init__()
        self.t = msec

    def start(self):
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(self.t)
        self.timer.timeout.connect(self.finished)
        self.timer.start()

    @QtCore.pyqtSlot()
    def interrupt(self):
        self.timer.stop()
        super().interrupt()


class QEvent(QProtocolEvent):

    def __init__(self, pydra, event, event_kw=None):
        super().__init__()
        self.pydra = pydra
        self.event = event
        self.event_kw = event_kw if event_kw else {}

    def start(self):
        self.pydra.send_event(self.event, **self.event_kw)
        self.finished.emit()


class QFreerun(QProtocolEvent):

    def __init__(self):
        super().__init__()


class QProtocol(QtCore.QObject):
    """Class for building and running protocols in Qt."""

    finished = QtCore.pyqtSignal()
    interrupted = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.event_queue = []
        self.current_event = None

    def run(self):
        self.next()

    @QtCore.pyqtSlot()
    def next(self):
        if len(self.event_queue):
            self.current_event = self.event_queue.pop(0)
            self.interrupted.connect(self.current_event.interrupt)
            self.current_event.finished.connect(self.next)
            self.current_event.finished.connect(self.current_event.deleteLater)
            self.current_event.start()
        else:
            self.finished.emit()

    @QtCore.pyqtSlot()
    def interrupt(self):
        self.current_event.finished.disconnect(self.next)
        self.interrupted.emit()

    def addPause(self, t):
        self.event_queue.append(QPause(t))

    def addEvent(self, pydra, name, kw=None):
        self.event_queue.append(QEvent(pydra, name, kw))

    def addFreerun(self):
        self.event_queue.append(QFreerun())


def build_qprotocol(pydra, protocol_events: typing.List[events.PROTOCOL_EVENT]) -> QProtocol:
    protocol = QProtocol()
    for event in protocol_events:
        event.add(pydra, protocol)
    return protocol
