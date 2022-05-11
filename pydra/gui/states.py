from PyQt5 import QtCore


class StateMachine(QtCore.QObject):

    _instance = None

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
