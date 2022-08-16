from PyQt5 import QtCore

from .state_machine import Stateful
from ..protocol import Protocol, events, build_protocol


def connect_signal(method, signal):
    def wrapper(*args, **kwargs):
        result = method(*args, **kwargs)
        signal.emit(result)
        return result
    return wrapper


class PydraInterface(Stateful, QtCore.QObject):

    newData = QtCore.pyqtSignal(dict)

    def __init__(self, pydra):
        super().__init__()
        # Set the pydra instance
        self.pydra = pydra
        # Wrap pydra methods
        self.pydra.receive_data = connect_signal(self.pydra.receive_data, self.newData)
        # Protocol
        self.protocol_ = None
        # Check for pydra and protocol updates
        self.stateMachine.update_timer.timeout.connect(self.fetch_messages)
        self.stateMachine.update_timer.timeout.connect(self.check_protocol_status)
        # Handle state transitions
        self.stateMachine.ready_to_start.entered.connect(self.enterReady)
        self.stateMachine.interrupted.entered.connect(self.enterInterrupted)

    def __getattr__(self, item):
        return getattr(self.pydra, item)

    @QtCore.pyqtSlot()
    def fetch_messages(self):
        """Polls pydra for new data and dispatches requests."""
        self.pydra.poll()
        self.pydra.send_request("data")

    @QtCore.pyqtSlot(str, str, dict)
    def send_event(self, target, event_name, event_kw):
        self.pydra.send_event(event_name, target=target, **event_kw)

    def _make_protocol(self) -> Protocol:
        protocol_list = list(self.protocol)
        directory = str(self.directory)
        filename = str(self.filename)
        trial_number = int(self.trial_number)
        # Add start recording to protocol
        protocol_list.insert(0, events.EVENT("start_recording",
                                             dict(directory=directory, filename=filename, idx=trial_number)))
        # Add stop recording to protocol
        protocol_list.append(events.EVENT("stop_recording"))
        # Create protocol
        protocol = build_protocol(self.pydra, protocol_list)
        return protocol

    @QtCore.pyqtSlot()
    def trigger_experiment_start(self):
        """Emits the start_experiment signal from the stateMachine, triggering the running state."""
        self.stateMachine.start_experiment.emit()

    @QtCore.pyqtSlot()
    def trigger_recording_start(self):
        """Emits the start_recording signal from the stateMachine, triggering the recording state"""
        self.stateMachine.start_recording.emit()

    @QtCore.pyqtSlot()
    def check_protocol_status(self) -> bool:
        try:
            if self.protocol_.is_running():
                return True
        except AttributeError:
            return False
        self.stateMachine.recording_finished.emit()
        return False

    def enterRunning(self):
        self.stateMachine.set_trial_index(0)

    def enterReady(self):
        """Ensures entry into the recording state when running state is entered."""
        self.trigger_recording_start()

    def enterInterrupted(self):
        """Interrupts the protocol"""
        if self.check_protocol_status():
            self.protocol_.interrupt()
            self.pydra.send_event("stop_recording")
        self.stateMachine.experiment_finished.emit()

    def startRecord(self):
        self.stateMachine.set_trial_index(self.trial_index + 1)
        self.protocol_ = self._make_protocol()
        self.protocol_.run()

    def startWait(self):
        if self.trial_index < self.n_trials:
            self.wait_timer = QtCore.QTimer()
            self.wait_timer.setSingleShot(True)
            self.wait_timer.timeout.connect(self.trigger_recording_start)
            self.wait_timer.start(self.inter_trial_interval)
            return
        self.stateMachine.experiment_finished.emit()
