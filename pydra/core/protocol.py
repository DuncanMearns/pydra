from PyQt5 import QtCore
from .trigger import Trigger, FreeRunningMode


class Queued(QtCore.QObject):
    """Class for queueing methods and other callables in a Protocol."""

    finished = QtCore.pyqtSignal()

    def __init__(self, method, *args, **kwargs):
        super().__init__()
        self.method = method
        self.args = args
        self.kwargs = kwargs

    def interrupt(self):
        return

    def __call__(self, *args, **kwargs):
        self.method(*self.args, **self.kwargs)
        self.finished.emit()


class Timer(QtCore.QObject):
    """Class for introducing waits in a Protocol."""

    finished = QtCore.pyqtSignal()

    def __init__(self, msec):
        super().__init__()
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(msec)
        self.timer.timeout.connect(self.timeout)

    def interrupt(self):
        self.timer.stop()

    def timeout(self):
        self.finished.emit()

    def __call__(self, *args, **kwargs):
        self.timer.start()


class TriggerContainer(QtCore.QObject):
    """Class for introducing triggers in a Protocol."""

    finished = QtCore.pyqtSignal()
    interrupted = QtCore.pyqtSignal()
    timeout = QtCore.pyqtSignal()

    def __init__(self, trigger):
        super().__init__()
        self.trigger = trigger
        self.trigger.triggered.connect(self.trigger_received)
        self.trigger.timeout.connect(self.timed_out)
        self.interrupted.connect(self.trigger.interrupt)

    def trigger_received(self):
        print("trigger received")
        self.finished.emit()

    def interrupt(self):
        self.interrupted.emit()

    def timed_out(self):
        self.timeout.emit()

    def __call__(self):
        self.trigger()


class Protocol(QtCore.QObject):
    """Class for creating and running protocols.

    Protocols are a queued sequence of events, timers and triggers. Events can be any callable method or function,
    timers introduce waits within the protocol, and triggers allow external triggers to be received before continuing.
    Protocols also allow for a "free-running mode", which will cause the protocol to run continuously until interrupted.

    Protocols may be repeated any number of times with a time gap in between repetitions.

    Parameters
    ----------
    name : str
        The name of the protocol.
    repetitions : int
        Number of times protocol is to be repeated.
    interval : float
        Time between repetitions of the protocol.

    Attributes
    ----------
    event_queue : list
        A list of events, timers and triggers within the protocol.
    rep : int
        The current repetition number.
    timer : QtCore.QTimer
        Timer for controlling interval between repetitions.
    flag : bool
        Internal flag for whether the protocol is currently running (includes repetitions and inter-rep intervals).

    Class Attributes
    ----------------
    completed : QtCore.pyqtSignal
        Qt signal emitted when all repetitions of the protocol are completed.
    finished : QtCore.pyqtSignal
        Qt signal emitted when one repetition of the protocol has ended.
    started : QtCore.pyqtSignal
        Qt signal emitted when a repetition of the protocol begins.
    interrupted : QtCore.pyqtSignal
        Qt signal emitted if the protocol is interrupted by an external or internal event (e.g. a trigger timing out).

    Notes
    -----
    The event queue is a list of Queued, Timer and TriggerContainer objects. These objects all implement a __call__
    method and contain a "finished" Qt signal. The finished signal of each object connect to the __call__ method of
    the next object in the event queue.
        * For Queued object, the finished signal emits as soon as the queued method returns.
        * For Timer objects, the finished signal emits after a predefined elapsed time.
        * For TriggerContainer objects, the finished signal emits when the Trigger object emits its triggered signal.
    The free-running mode implements a special case of a TriggerContainer, whereby a trigger is never received and so
    a finished signal is never emitted.
    """

    completed = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal(int)
    started = QtCore.pyqtSignal(int)
    interrupted = QtCore.pyqtSignal()

    def __init__(self, name, repetitions, interval):
        super().__init__()
        self.name = name
        self.repetitions = repetitions
        self.interval = interval
        self.event_queue = []
        self.rep = 0
        # Inter-protocol timer
        self.timer = QtCore.QTimer()
        self.timer.setInterval(int(self.interval * 1000))
        self.timer.setSingleShot(True)
        # Running attribute
        self.flag = False
        self.started.connect(self.setFlag)
        self.completed.connect(self.clearFlag)

    def addEvent(self, method: callable, *args, **kwargs) -> None:
        """Add an event to the protocol.

        Parameters
        ----------
        method : callable
            Any object that implements a __call__ method.
        args : iterable
            Arguments passed to method when called.
        kwargs : dict
            Keyword arguments passed to method when called.
        """
        event = Queued(method, *args, **kwargs)
        self._add(event)

    def addTimer(self, msec: int) -> None:
        """Add a timer to the protocol.

        Parameters
        ----------
        msec : int
            The duration of the timer (in milliseconds).
        """
        timer = Timer(msec)
        self._add(timer)

    def addTrigger(self, trigger: Trigger) -> None:
        """Add a timer to the protocol.

        Parameters
        ----------
        trigger : Trigger
            A Trigger object.
        """
        container = TriggerContainer(trigger)
        container.timeout.connect(self.interrupt)
        self._add(container)

    def freeRunningMode(self):
        """Cause protocol to enter free-running mode. No events, timers or triggers can be called after protocol enters
        free-running mode."""
        self.addTrigger(FreeRunningMode())

    def _add(self, queued):
        """Private method to add events, timers and triggers to the event queue."""
        if len(self.event_queue):
            self.event_queue[-1].finished.connect(queued.__call__)
        self.event_queue.append(queued)

    def start(self):
        """Called to start one repetition of the protocol."""
        self.rep += 1
        self.started.emit(self.rep)
        self.event_queue[0]()

    def end(self):
        """Called at the end of a repetition of the protocol."""
        self.finished.emit(self.rep)
        if self.rep < self.repetitions:
            self.timer.start()
        else:
            self.completed.emit()

    def interrupt(self):
        """Interrupts the protocol."""
        self.timer.stop()
        for event in self.event_queue:
            event.interrupt()
        self.interrupted.emit()
        self.finished.emit(self.rep)
        self.completed.emit()

    def __call__(self, *args, **kwargs):
        self.rep = 0
        if len(self.event_queue):
            self.timer.timeout.connect(self.start)
            self.event_queue[-1].finished.connect(self.end)
            self.start()

    def setFlag(self):
        """Sets the flag. Internal use only."""
        self.flag = True

    def clearFlag(self):
        """Clears the flag. Internal use only."""
        self.flag = False

    def running(self):
        """Returns whether the protocol is running (includes repetitions and inter-rep intervals)."""
        return self.flag
