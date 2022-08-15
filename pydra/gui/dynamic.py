import numpy as np
from PyQt5 import QtCore
from ..utils.cache import TempCache


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
                           "trial_index": int}

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


class StateMachine(QtCore.QObject, metaclass=StateMachineMeta):
    """Single class that handles shared state within the GUI. Contains a QStateMachine object and attributes that can
    be accessed through classes that inherit from Stateful."""

    _instance = None

    # Experiment signals
    start_experiment = QtCore.pyqtSignal()  # emitted when experiment is started
    start_recording = QtCore.pyqtSignal()  # emitted when trial starts recording
    recording_finished = QtCore.pyqtSignal()  # emitted when recording finishes
    experiment_finished = QtCore.pyqtSignal()  # emitted when experiment finishes

    # # Protocol signals
    # protocol_changed = QtCore.pyqtSignal(list)

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
        # Waiting state - waiting for a recording to begin
        self.waiting = QtCore.QState(self.running)
        # Recording state - recording currently in progress
        self.recording = QtCore.QState(self.running)
        self.running.setInitialState(self.waiting)
        # Add states to state maching
        self._stateMachine.addState(self.idle)
        self._stateMachine.addState(self.running)
        # Add transitions
        self.idle.addTransition(self.start_experiment, self.running)
        self.running.addTransition(self.experiment_finished, self.idle)
        self.waiting.addTransition(self.start_recording, self.recording)
        self.recording.addTransition(self.recording_finished, self.waiting)
        # =============================
        # Dynamic experiment attributes
        # =============================
        self.set_directory("")
        self.set_filename("")
        self.set_trial_number(1)
        self.set_trial_index(0)
        self.set_n_trials(1)
        self.set_inter_trial_interval(0)  # ms
        # ================
        # GUI update timer
        # ================
        self.update_interval = 30
        self.update_timer = QtCore.QTimer()
        self.update_timer.setInterval(self.update_interval)

    def start(self):
        """Starts the QtStateMachine. Should only be called once."""
        self._stateMachine.setInitialState(self.idle)
        self._stateMachine.start()
        self.update_timer.start()


class Stateful:

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


class GUICache(TempCache):

    def __init__(self, cachesize, arr_cachesize):
        super().__init__(cachesize, arr_cachesize)

    def update(self, new_data):
        for key, val in new_data.items():
            try:
                self.__getattribute__("new_" + key)(val)
            except AttributeError:
                setattr(self, key, val)

    def new_data(self, data: dict):
        # for k, vals in data.items():
        #     print(k, vals)
        return

    def new_array(self, arr: np.ndarray):
        return

    def new_events(self, events: list):
        for t, data in events:
            self.append_event(t, data)
        return


class DynamicUpdate:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cachesize = kwargs.get("cachesize")
        arr_cachesize = kwargs.get("arr_cachesize", cachesize)
        self.cache = GUICache(cachesize, arr_cachesize)

    def dynamicUpdate(self):
        return
