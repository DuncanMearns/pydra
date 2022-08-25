from PyQt5 import QtCore

from .state_machine import Stateful
from ..protocol import Protocol, events, build_protocol


def connect_signal(method, signal):
    """Decorator for Pydra methods that connects them to a Qt signal."""
    def wrapper(*args, **kwargs):
        result = method(*args, **kwargs)
        signal.emit(*result)
        return result
    return wrapper


class PydraInterface(Stateful, QtCore.QObject):
    """Class that allows GUI to interface with Pydra. Enables Pydra protocols to be run and controlled from the GUI, and
    allows incoming data from Pydra to be broadcast to other GUI components. Has access to shared experiment state and
    associated attributes via Stateful.

    Parameters
    ----------
    pydra :
        The Pydra instance.
    """

    _new_data = QtCore.pyqtSignal(dict, dict)
    update_gui = QtCore.pyqtSignal(dict)

    def __init__(self, pydra):
        super().__init__()
        # Set the pydra instance
        self.pydra = pydra
        # Protocol
        self.protocol_ = None
        # Connect signals
        self.pydra.receive_data = connect_signal(self.pydra.receive_data, self._new_data)
        self._new_data.connect(self.data_from_backend)
        self._received_from = []
        # Fast gui update
        self.stateMachine.gui_update.connect(self.poll_messages)
        self.stateMachine.gui_update.connect(self.check_protocol_status)
        # Handle state transitions
        self.stateMachine.ready_to_start.entered.connect(self.enterReady)
        self.stateMachine.interrupted.entered.connect(self.enterInterrupted)
        # Request data
        self.request_data()

    def __getattr__(self, item):
        return getattr(self.pydra, item)

    @property
    def savers(self):
        return [saver.name for saver in self.pydra.savers]

    @QtCore.pyqtSlot()
    def request_data(self):
        """Requests new data from pydra."""
        self.pydra.send_request("data")

    @QtCore.pyqtSlot()
    def poll_messages(self):
        """Polls pydra for new data."""
        self.pydra.poll()

    @QtCore.pyqtSlot(dict, dict)
    def data_from_backend(self, data, msg_tags):
        source = msg_tags["source"]
        self._received_from.append(source)
        if all([saver in self._received_from for saver in self.savers]):  # all savers have updated
            self._received_from = []
            self.request_data()
        self.update_gui.emit(data)

    @QtCore.pyqtSlot(str, str, dict)
    def send_event(self, target, event_name, event_kw):
        """Slot for broadcasting event messages to the Pydra network."""
        self.pydra.send_event(event_name, target=target, **event_kw)

    def _make_protocol(self) -> Protocol:
        """Returns a complete Protocol containing the current protocol event list."""
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
        """Checks whether a protocol is currently running. Emits a recording_finished signal from the state machine if
        a protocol is no longer running."""
        try:
            if self.protocol_.is_running():
                return True
        except AttributeError:
            return False
        self.stateMachine.recording_finished.emit()
        return False

    def enterRunning(self):
        """Set the trial index to zero."""
        self.stateMachine.set_trial_index(0)

    def enterReady(self):
        """Ensures entry into the recording state when running state is entered."""
        self.trigger_recording_start()

    def enterInterrupted(self):
        """Interrupts the protocol when GUI enters the interrupted state and emit an experiment_finished signal."""
        if self.check_protocol_status():
            self.protocol_.interrupt()
            self.pydra.send_event("stop_recording")
        self.stateMachine.experiment_finished.emit()

    def startRecord(self):
        """Increment the trial index, then create and run a protocol when GUI enters the recording state."""
        self.stateMachine.set_trial_index(self.trial_index + 1)
        self.protocol_ = self._make_protocol()
        self.protocol_.run()

    def startWait(self):
        """Starts a wait timer if there are still more trials to run, otherwise emits an experiment_finished signal."""
        if self.trial_index < self.n_trials:
            self.wait_timer = QtCore.QTimer()
            self.wait_timer.setSingleShot(True)
            self.wait_timer.timeout.connect(self.trigger_recording_start)
            self.wait_timer.start(self.inter_trial_interval)
            return
        self.stateMachine.experiment_finished.emit()
