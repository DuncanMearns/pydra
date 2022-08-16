import time
from PyQt5 import QtCore


def shared_state_setter(attr, _type):
    def attr_setter(instance, value):
        setattr(instance, attr, value)
        getattr(instance, attr + "_changed").emit(value)
    return attr_setter


def shared_state_getter(attr):
    def attr_getter(instance):
        return getattr(instance.stateMachine, attr)
    return attr_getter


class StateMachineMeta(type(QtCore.QObject)):
    """Qt metaclass for StateMachine. Contains _dynamic_attributes that can be set using the set_name slot, and emit
    a name_changed signal whenever changed. These attributes can be accessed by any class inheriting from Stateful."""

    _dynamic_attributes = {"directory": str,
                           "filename": str,
                           "trial_number": int,
                           "n_trials": int,
                           "inter_trial_interval": int,
                           "trial_index": int,
                           "protocol": list}

    def __new__(cls, name, bases, dct):
        """Dynamically create signals and slots for dynamic attributes."""
        for attr, attr_type in cls._dynamic_attributes.items():
            # Create signal
            signal_name = attr + "_changed"
            dct[signal_name] = QtCore.pyqtSignal(attr_type, name=signal_name)
            # Create setter slot
            setter_name = "set_" + attr
            dct[setter_name] = QtCore.pyqtSlot(attr_type, name=setter_name)(shared_state_setter(attr, attr_type))
        return super().__new__(cls, name, bases, dct)


class Timer(QtCore.QObject):

    def __init__(self):
        super().__init__()
        self._t0 = 0
        self._running = False
        self._last = 0

    @QtCore.pyqtSlot()
    def start(self):
        self._t0 = time.perf_counter()
        self._running = True

    @QtCore.pyqtSlot()
    def stop(self):
        self._running = False

    @property
    def t0(self) -> float:
        return self._t0

    @property
    def time(self) -> float:
        if self._running:
            self._last = time.perf_counter() - self.t0
        return self._last


class StateMachine(QtCore.QObject, metaclass=StateMachineMeta):
    """Singleton class that handles shared state within the GUI. Contains a QStateMachine object and attributes that can
    be accessed through classes that inherit from Stateful."""

    _instance = None

    # Experiment signals
    start_experiment = QtCore.pyqtSignal()  # emitted when experiment is started
    start_recording = QtCore.pyqtSignal()  # emitted when trial starts recording
    recording_finished = QtCore.pyqtSignal()  # emitted when recording finishes
    experiment_finished = QtCore.pyqtSignal()  # emitted when experiment finishes
    interrupt = QtCore.pyqtSignal()  # emitted when an experiment is interrupted

    def __new__(cls, *args, **kwargs):
        if cls._instance:
            raise TypeError("Cannot create more than once instance of StateMachine")
        cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        # =============
        # State machine
        # =============
        self._stateMachine = QtCore.QStateMachine()
        # Idle state - gui completely active
        self.idle = QtCore.QState()
        # Running state - restricted gui functionality
        self.running = QtCore.QState()
        # Ready to start - intermediate state before first recording begins
        self.ready_to_start = QtCore.QState(self.running)
        self.running.setInitialState(self.ready_to_start)
        # Waiting state - waiting for a recording to begin
        self.waiting = QtCore.QState(self.running)
        # Recording state - recording currently in progress
        self.recording = QtCore.QState(self.running)
        # Interrupted state - an experiment has been interrupted
        self.interrupted = QtCore.QState(self.running)
        # Add states to state maching
        self._stateMachine.addState(self.idle)
        self._stateMachine.addState(self.running)
        # Add transitions
        self.idle.addTransition(self.start_experiment, self.running)
        self.running.addTransition(self.experiment_finished, self.idle)
        self.ready_to_start.addTransition(self.start_recording, self.recording)
        self.waiting.addTransition(self.start_recording, self.recording)
        self.recording.addTransition(self.recording_finished, self.waiting)
        self.recording.addTransition(self.interrupt, self.interrupted)
        self.waiting.addTransition(self.interrupt, self.interrupted)
        # =============================
        # Dynamic experiment attributes
        # =============================
        # Ensure all dynamic attributes are initialized
        for attr, attr_type in StateMachine._dynamic_attributes.items():
            getattr(self, "set_" + attr)(attr_type())
        # ================
        # GUI update timer
        # ================
        self.update_interval = 30
        self.update_timer = QtCore.QTimer()
        self.update_timer.setInterval(self.update_interval)
        # =============
        # Global timers
        # =============
        # Experiment timer
        self.experiment_timer = Timer()
        self.running.entered.connect(self.experiment_timer.start)
        self.running.exited.connect(self.experiment_timer.stop)
        # Recording timer
        self.trial_timer = Timer()
        self.recording.entered.connect(self.trial_timer.start)
        self.recording.exited.connect(self.trial_timer.stop)
        # Wait timer
        self.wait_timer = Timer()
        self.waiting.entered.connect(self.wait_timer.start)
        self.waiting.exited.connect(self.wait_timer.stop)

    def start(self):
        """Starts the QtStateMachine. Should only be called once."""
        self._stateMachine.setInitialState(self.idle)
        self._stateMachine.start()
        self.update_timer.start()

    def check_state(self, state):
        if state in self._stateMachine.configuration():
            return True
        return False


class Stateful:
    """Mixin for GUI components that share state and dynamic attributes, accessed via the stateMachine property."""

    _state_machine = StateMachine()

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls, *args, **kwargs)
        for attr, val in StateMachine._dynamic_attributes.items():
            setattr(cls, attr, property(shared_state_getter(attr)))
        return instance

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stateMachine.idle.entered.connect(self.enterIdle)
        self.stateMachine.running.entered.connect(self.enterRunning)
        self.stateMachine.recording.entered.connect(self.startRecord)
        self.stateMachine.recording.exited.connect(self.stopRecord)
        self.stateMachine.waiting.entered.connect(self.startWait)

    @property
    def stateMachine(self):
        return self._state_machine

    @property
    def timers(self) -> dict:
        return {
            "experiment": self.stateMachine.experiment_timer,
            "trial": self.stateMachine.trial_timer,
            "wait": self.stateMachine.wait_timer
        }

    def is_idle(self):
        return self.stateMachine.check_state(self.stateMachine.idle)

    def is_running(self):
        return self.stateMachine.check_state(self.stateMachine.running)

    def is_recording(self):
        return self.stateMachine.check_state(self.stateMachine.recording)

    def is_waiting(self):
        return self.stateMachine.check_state(self.stateMachine.waiting)

    def enterIdle(self):
        pass

    def enterRunning(self):
        pass

    def startRecord(self):
        pass

    def stopRecord(self):
        pass

    def startWait(self):
        pass
