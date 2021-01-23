from PyQt5 import QtCore


class StateEnabled:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setIdle(self):
        for child in self.children():
            if issubclass(type(child), StateEnabled):
                child.setIdle()

    def setRecord(self):
        for child in self.children():
            if issubclass(type(child), StateEnabled):
                child.setRecord()

    def endRecord(self):
        for child in self.children():
            if issubclass(type(child), StateEnabled):
                child.endRecord()

    def _create_state_machine(self):
        """Creates the state machine. Should only be called once at the beginning of the main window constructor."""
        self.stateMachine = QtCore.QStateMachine()
        self.idleState = QtCore.QState()
        self.recordState = QtCore.QState()
        # Idle
        self.idleState.entered.connect(self.setIdle)
        self.stateMachine.addState(self.idleState)
        # Record
        self.recordState.entered.connect(self.setRecord)
        self.recordState.exited.connect(self.endRecord)
        self.stateMachine.addState(self.recordState)

    def _start_state_machine(self):
        """Starts the state machine. Should only be called once at the end of the main window constructor."""
        self.stateMachine.setInitialState(self.idleState)
        self.stateMachine.start()
