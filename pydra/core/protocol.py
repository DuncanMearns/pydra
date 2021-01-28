from PyQt5 import QtCore


class Queued(QtCore.QObject):
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


class Protocol(QtCore.QObject):

    completed = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal(int)
    started = QtCore.pyqtSignal(int)

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

    def addEvent(self, method, *args, **kwargs):
        event = Queued(method, *args, **kwargs)
        self._add(event)

    def addTimer(self, msec):
        timer = Timer(msec)
        self._add(timer)

    def _add(self, queued):
        if len(self.event_queue):
            self.event_queue[-1].finished.connect(queued.__call__)
        self.event_queue.append(queued)

    def interrupt(self):
        self.timer.stop()
        for event in self.event_queue:
            event.interrupt()
        self.completed.emit()

    def start(self):
        self.rep += 1
        self.started.emit(self.rep)
        self.event_queue[0]()

    def end(self):
        self.finished.emit(self.rep)
        if self.rep < self.repetitions:
            self.timer.start()
        else:
            self.completed.emit()

    def __call__(self, *args, **kwargs):
        self.rep = 0
        if len(self.event_queue):
            self.timer.timeout.connect(self.start)
            self.event_queue[-1].finished.connect(self.end)
            self.start()
