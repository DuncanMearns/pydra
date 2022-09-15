"""Module for handling shared state within the Pydra GUI."""
import time
from PyQt5 import QtCore
from .default_params import default_params

__all__ = ("Stateful",)


_state_attrs = {
    "recording_triggers": (None, None),
    "inter_trial_ms": 0,
    "trial_index": 0,
    "event_names": [],
    "targets": [],
    "triggers": {},
    "protocol": []
}


def shared_state_setter(attr, _type):
    """Returns a setter for a dynamic attribute."""
    def attr_setter(instance, value):
        setattr(instance, attr, value)
        getattr(instance, attr + "_changed").emit(value)
    return attr_setter


def shared_state_getter(attr):
    """Returns a getter for a dynamic attribute."""
    def attr_getter(instance):
        return getattr(instance.stateMachine, attr)
    return attr_getter


class StateMachineMeta(type(QtCore.QObject)):
    """Qt metaclass for StateMachine. Contains _dynamic_attributes that can be set using the set_name slot, and emit
    a name_changed signal whenever changed. These attributes can be accessed by any class inheriting from Stateful."""

    _dynamic_attributes = dict([(param, type(val)) for param, val in default_params.items()] +
                               [(param, type(val)) for param, val in _state_attrs.items()])

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
    """Implements a simple timer."""

    def __init__(self):
        super().__init__()
        self._t0 = 0
        self._running = False
        self._last = 0

    @QtCore.pyqtSlot()
    def start(self):
        """Start the timer."""
        self._t0 = time.perf_counter()
        self._running = True

    @QtCore.pyqtSlot()
    def stop(self):
        """Stop the timer."""
        self._running = False

    @property
    def t0(self) -> float:
        """Stores the time the timer was started."""
        return self._t0

    @property
    def time(self) -> float:
        """Stores how long the timer has been running (or how long it was running if it has stopped)."""
        if self._running:
            self._last = time.perf_counter() - self.t0
        return self._last


class StateMachine(QtCore.QObject, metaclass=StateMachineMeta):
    """Singleton class that handles shared state within the GUI. Contains a QStateMachine object and attributes that can
    be accessed through subclasses of Stateful.

    Attributes
    ----------
    idle : QtCore.QState
        Idle state. No experiment is currently running, GUI is completely responsive.
    running : QtCore.QState
        Running state. An experiment is currently running, limited GUI functionality.
    waiting : QtCore.QState
        Waiting state.  Sub-state of running. An experiment protocol is running, but not currently recording.
    recording : QtCore.QState
        Recording state. Sub-state of running. A recording is in progress.
    ready_to_start : QtCore.QState
        Temporary initial sub-state of running, entered just before the first recording of an experiment starts.
    interrupted : QtCore.QState
        Temporary sub-state of running, entered when an experiment is manually interrupted by user.
    update_timer : QtCore.QTimer
        QTimer that controls GUI update. Timeout connected to the gui_update signal.
    experiment_timer : Timer
        Records how long an experiment has been running.
    trial_timer : Timer
        Records how long a trial has been running.
    wait_timer : Timer
        Records how long an inter-trial period has been running.
    """

    _instance = None  # singleton instance, only initialized once when the StateMachine class if first instantiated.

    # Experiment signals
    start_experiment = QtCore.pyqtSignal()  # emitted when experiment is started
    start_recording = QtCore.pyqtSignal()  # emitted when trial starts recording
    recording_finished = QtCore.pyqtSignal()  # emitted when recording finishes
    experiment_finished = QtCore.pyqtSignal()  # emitted when experiment finishes
    interrupt = QtCore.pyqtSignal()  # emitted when an experiment is interrupted

    # Timer signals
    gui_update = QtCore.pyqtSignal()

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
        # ================
        # GUI update timer
        # ================
        self.update_interval = 30
        self.update_timer = QtCore.QTimer()
        self.update_timer.setInterval(self.update_interval)
        self.update_timer.timeout.connect(self.gui_update)
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
        """Starts the StateMachine. Should only be called once."""
        self.set_params(_state_attrs)
        self._stateMachine.setInitialState(self.idle)
        self._stateMachine.start()
        self.update_timer.start()

    def check_state(self, state: QtCore.QState) -> bool:
        """Check if the state machine is currently in the given state."""
        if state in self._stateMachine.configuration():
            return True
        return False

    def set_params(self, gui_params: dict):
        # Ensure all dynamic attributes are initialized
        for attr, val in gui_params.items():
            getattr(self, "set_" + attr)(val)


class Stateful:
    """Mixin for GUI components that share state and dynamic attributes, accessed via the stateMachine property."""

    _state_machine = StateMachine()

    def __new__(cls, *args, **kwargs):
        """Allow access to _dynamic_attributes of StateMachine."""
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
    def stateMachine(self) -> StateMachine:
        """Property to access the instance of the state machine."""
        return self._state_machine

    @property
    def timers(self) -> dict:
        """Property to access state machine timers. Has keys 'experiment', 'trial' and 'wait'."""
        return {
            "experiment": self.stateMachine.experiment_timer,
            "trial": self.stateMachine.trial_timer,
            "wait": self.stateMachine.wait_timer
        }

    def is_idle(self) -> bool:
        """Returns whether the state machine is currently in the idle state."""
        return self.stateMachine.check_state(self.stateMachine.idle)

    def is_running(self) -> bool:
        """Returns whether the state machine is currently in the running state."""
        return self.stateMachine.check_state(self.stateMachine.running)

    def is_recording(self) -> bool:
        """Returns whether the state machine is currently in the recording state."""
        return self.stateMachine.check_state(self.stateMachine.recording)

    def is_waiting(self) -> bool:
        """Returns whether the state machine is currently in the waiting state."""
        return self.stateMachine.check_state(self.stateMachine.waiting)

    def enterIdle(self):
        """Called whenever the state machine enters the idle state. Override in subclasses."""
        pass

    def enterRunning(self):
        """Called whenever the state machine enters the running state. Override in subclasses."""
        pass

    def startRecord(self):
        """Called whenever the state machine enters the recording state. Override in subclasses."""
        pass

    def stopRecord(self):
        """Called whenever the state machine exits the recording state. Override in subclasses."""
        pass

    def startWait(self):
        """Called whenever the state machine enters the waiting state. Override in subclasses."""
        pass
