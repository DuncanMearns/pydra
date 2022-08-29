from PyQt5 import QtWidgets, QtCore
from ..state_machine import Stateful


class TriggerInterface(Stateful, QtWidgets.QWidget):

    triggered = QtCore.pyqtSignal(bool)

    def __init__(self, name, thread):
        super().__init__()
        # Set the thread attribute and connect triggered signal
        self.name = name
        self.thread = thread
        self.stateMachine.gui_update.connect(self.check_trigger_state)
        self.triggered.connect(self.set_trigger_appearance)
        # Create layout and add widgets
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().addWidget(QtWidgets.QLabel(self.name))
        self.state_button = QtWidgets.QPushButton("")
        self.state_button.setEnabled(False)
        self.layout().addWidget(self.state_button)
        self.reset_button = QtWidgets.QPushButton("reset")
        self.reset_button.clicked.connect(self.reset_trigger)
        self.layout().addWidget(self.reset_button)
        self.manual_button = QtWidgets.QPushButton("trigger")
        self.manual_button.clicked.connect(self.manual_trigger)
        self.layout().addWidget(self.manual_button)

    @QtCore.pyqtSlot()
    def check_trigger_state(self):
        """Emits the current state of the trigger."""
        trigger_state = self.thread.event_flag.is_set()
        self.triggered.emit(trigger_state)

    @QtCore.pyqtSlot(bool)
    def set_trigger_appearance(self, trigger_state):
        """Sets the appearance of the trigger state button."""
        if trigger_state:
            self.state_button.setText("TRIGGERED")
            self.state_button.setStyleSheet(self.triggered_style())
        else:
            self.state_button.setText("WAITING")
            self.state_button.setStyleSheet(self.waiting_style())

    @QtCore.pyqtSlot()
    def reset_trigger(self):
        """Resets the trigger."""
        self.thread.reset()

    @QtCore.pyqtSlot()
    def manual_trigger(self):
        """Manually activates the trigger."""
        self.thread.event_flag.set()

    @staticmethod
    def waiting_style():
        return "background-color:red"

    @staticmethod
    def triggered_style():
        return "background-color:cyan"


class TriggersWidget(QtWidgets.QGroupBox):
    """Widget containing state of triggers in experiment.

    Parameters
    ----------
    triggers : dict
        Dictionary of trigger threads from pydra.
    """

    def __init__(self, triggers: dict, **kwargs):
        super().__init__("Triggers")
        self.triggers = triggers
        self.setLayout(QtWidgets.QVBoxLayout())
        self._widgets = []
        for name, thread in self.triggers.items():
            widget = TriggerInterface(name, thread)
            self._widgets.append(widget)
            self.layout().addWidget(widget)
