from PyQt5 import QtCore


class StateEnabled:

    def _create_state_machine(self):
        """Creates the state machine. Should only be called once at the beginning of the main window constructor."""
        # State machine
        self.stateMachine = QtCore.QStateMachine()  # state machine
        # Idle state - gui completely active
        self.idleState = QtCore.QState()
        self.idleState.entered.connect(self.enterIdle)
        self.stateMachine.addState(self.idleState)
        # Running state - restricted gui functionality
        self.runningState = QtCore.QState()
        self.recordState = QtCore.QState(self.runningState)
        self.waitingState = QtCore.QState(self.runningState)
        self.runningState.setInitialState(self.recordState)
        self.runningState.entered.connect(self.enterRunning)
        self.recordState.entered.connect(self.enterRecord)
        self.recordState.exited.connect(self.exitRecord)
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

    def enterRecord(self):
        for child in self.children():
            if issubclass(type(child), StateEnabled):
                child.enterRecord()

    def exitRecord(self):
        for child in self.children():
            if issubclass(type(child), StateEnabled):
                child.exitRecord()
