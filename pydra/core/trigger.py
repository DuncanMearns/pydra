from PyQt5 import QtCore
import zmq


class ExternalTrigger(QtCore.QThread):

    timeout = QtCore.pyqtSignal()
    triggered = QtCore.pyqtSignal()

    def __init__(self, timeout=None):
        super().__init__()
        self._timeout = timeout  # ms

    def __call__(self):
        self.start()

    def run(self) -> None:
        self.setup()
        self.timer = QtCore.QTimer()
        self.timer.setInterval(1)
        self.timer.timeout.connect(self.check)
        self.timer.start()
        if self._timeout:
            self._timeout_timer = QtCore.QTimer()
            self._timeout_timer.setInterval(self._timeout)
            self._timeout_timer.setSingleShot(True)
            self._timeout_timer.timeout.connect(self.timed_out)
            self._timeout_timer.start()
        self.exec()

    def setup(self):
        print("waiting for trigger")

    def check(self):
        self.triggered.emit()

    def timed_out(self):
        self.timeout.emit()
        self.interrupt()

    def interrupt(self):
        self.quit()


class FreeRunningMode(ExternalTrigger):

    def __init__(self):
        super().__init__(timeout=None)

    def setup(self):
        pass

    def check(self):
        pass


class ZMQTrigger(ExternalTrigger):

    def __init__(self, port, timeout=None):
        super().__init__(timeout)
        self.port = port

    def setup(self):
        self._triggered = False
        self.ctx = zmq.Context.instance()
        self.sock = self.ctx.socket(zmq.SUB)
        self.sock.connect(self.port)
        self.sock.setsockopt(zmq.SUBSCRIBE, b"")
        super().setup()

    def check(self):
        try:
            if self.sock.poll(0):
                self.triggered.emit()
                self.interrupt()
        except zmq.error.ZMQError:
            pass

    def interrupt(self):
        self.sock.close()
        super().interrupt()
