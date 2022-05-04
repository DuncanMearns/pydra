from PyQt5 import QtCore


class StateMachine(QtCore.QObject):

    _instance = None
    # startRecord = QtCore.pyqtSignal(int)
    # stopRecord = QtCore.pyqtSignal(int)

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            return cls._instance
        else:
            raise TypeError("Cannot create more than once instance of StateMachine")

    def __init__(self):
        super().__init__()
        # State machine
        self._stateMachine = QtCore.QStateMachine()
        # Idle state - gui completely active
        self.idle = QtCore.QState()
        self._stateMachine.addState(self.idle)
        # Running state - restricted gui functionality
        self.running = QtCore.QState()
        self._stateMachine.addState(self.running)
        # Recording state
        self.recording = QtCore.QState()
        self.recording_number = 0
        self._stateMachine.addState(self.recording)

    def start(self):
        """Starts the QtStateMachine. Should only be called once."""
        self._stateMachine.setInitialState(self.idle)
        self._stateMachine.start()


class Stateful:

    _state_machine = StateMachine()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stateMachine.idle.entered.connect(self.enterIdle)
        self.stateMachine.running.entered.connect(self.enterRunning)
        self.stateMachine.recording.entered.connect(self.startRecord)
        self.stateMachine.recording.exited.connect(self.stopRecord)

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


class StateEnabled:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _create_state_machine(self):
        """Creates the state machine. Should only be called once at the beginning of the main window constructor."""
        # State machine
        self.stateMachine = QtCore.QStateMachine()
        # Idle state - gui completely active
        self.idleState = QtCore.QState()
        self.idleState.entered.connect(self.enterIdle)
        self.stateMachine.addState(self.idleState)
        # Running state - restricted gui functionality
        self.runningState = QtCore.QState()
        self.runningState.entered.connect(self.enterRunning)
        self.stateMachine.addState(self.runningState)

    def _start_state_machine(self):
        """Starts the state machine. Should only be called once at the end of the main window constructor."""
        self.stateMachine.setInitialState(self.idleState)
        self.stateMachine.start()

    def enterIdle(self):
        for child in self.children():
            if issubclass(type(child), StateEnabled):
                child.enterIdle()

    def enterRunning(self):
        for child in self.children():
            if issubclass(type(child), StateEnabled):
                child.enterRunning()

    def startRecord(self, i):
        for child in self.children():
            if issubclass(type(child), StateEnabled):
                child.startRecord(i)

    def endRecord(self, i):
        for child in self.children():
            if issubclass(type(child), StateEnabled):
                child.endRecord(i)
