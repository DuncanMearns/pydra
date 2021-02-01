from PyQt5 import QtCore
import zmq


class Trigger(QtCore.QThread):
    """Base class for receiving triggers in PyQt.

    Trigger objects are a type of QtCore.QThread that contain their own event loop. The event loop is started when the
    object is called.

    Parameters
    ----------
    timeout : int (optional)
        The timeout time of the trigger (in milliseconds).

    Notes
    -----
    When the thread begins, a setup method is called (allowing for resetting of attributes etc.). While the event loop
    is running, the Trigger object constantly checks whether a trigger has been received (via the check method). If a
    trigger has been received, the triggered signal may be emitted. If a timeout time has been specified, the thread
    will terminate after the specified time has elapsed. The class also implements an interrupt method, that allows the
    thread to be terminated by signal from another thread.
    """

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
        """Called after the thread starts but before the event loop starts. May be overridden in subclasses."""
        print("waiting for trigger")

    def check(self):
        """Method to check for the trigger. Should be overridden in subclasses."""
        self.triggered.emit()

    @QtCore.pyqtSlot()
    def timed_out(self):
        """Emits a timeout signal if the timeout time has elapsed, then tnterrupts the thread."""
        self.timeout.emit()
        self.interrupt()

    def interrupt(self):
        """Terminates the thread. Subclasses should include call to super."""
        self.quit()


class FreeRunningMode(Trigger):
    """A dummy Trigger class that never emits a triggered signal."""

    def __init__(self):
        super().__init__(timeout=None)

    def setup(self):
        pass

    def check(self):
        pass


class ZMQTrigger(Trigger):
    """Class for receiving triggers over 0MQ.

    Parameters
    ----------
    port : str
        The port over which to listen for triggers in a PUB/SUB pattern.
    """

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
