import os
from PyQt5 import QtCore

from .dynamic import Stateful
from ..protocol import Protocol, events, build_protocol


def connect_signal(method, signal):
    def wrapper(*args, **kwargs):
        result = method(*args, **kwargs)
        signal.emit(result)
        return result
    return wrapper


class PydraInterface(Stateful, QtCore.QObject):

    newData = QtCore.pyqtSignal(dict)

    def __init__(self, pydra, check_msec: int = 10):
        super().__init__()
        # Pydra
        self.pydra = pydra
        # Wrap pydra methods
        self.pydra.receive_data = connect_signal(self.pydra.receive_data, self.newData)
        # Trial
        self.stateMachine.directory_changed.connect(self.new_directory)
        self.stateMachine.filename_changed.connect(self.new_filename)
        self.stateMachine.trial_number_changed.connect(self.new_trial_number)
        self.stateMachine.n_trials_changed.connect(self.new_n_trials)
        self.stateMachine.inter_trial_interval_changed.connect(self.new_inter_trial_interval)
        # Protocol
        self.protocol_list = []
        self.protocol = None
        # Check for protocol updates
        self.stateMachine.update_timer.timeout.connect(self.check_protocol_status)

    def __getattr__(self, item):
        return getattr(self.pydra, item)

    @QtCore.pyqtSlot()
    def fetch_messages(self):
        """Polls pydra for new data and dispatches requests."""
        self.pydra.poll()
        self.pydra.send_request("data")

    @QtCore.pyqtSlot(str)
    def new_directory(self, val):
        print("Directory changed", val, self.directory)

    @QtCore.pyqtSlot(str)
    def new_filename(self, val):
        print("Filename changed", val, self.filename)

    @QtCore.pyqtSlot(int)
    def new_trial_number(self, val):
        print("Trial number changed", val, self.trial_number)

    @QtCore.pyqtSlot(int)
    def new_n_trials(self, val):
        print("N trials changed", val, self.n_trials)

    @QtCore.pyqtSlot(int)
    def new_inter_trial_interval(self, val):
        print("Inter trial interval changed", val, self.inter_trial_interval)

    @QtCore.pyqtSlot(list)
    def set_protocol(self, event_list):
        self.protocol_list = event_list

    @QtCore.pyqtSlot(str, str, dict)
    def send_event(self, target, event_name, event_kw):
        self.pydra.send_event(event_name, target=target, **event_kw)

    def _make_protocol(self) -> Protocol:
        protocol_list = list(self.protocol_list)
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
    def start_experiment(self):
        self.stateMachine.start_experiment.emit()

    @QtCore.pyqtSlot()
    def interrupt(self):
        self.protocol.interrupt()
        self.pydra.send_event("stop_recording")
        self.stateMachine.experiment_finished.emit()

    @QtCore.pyqtSlot()
    def start_protocol(self):
        self.stateMachine.start_recording.emit()

    @QtCore.pyqtSlot()
    def check_protocol_status(self) -> bool:
        try:
            if self.protocol.is_running():
                return True
        except AttributeError:
            return False
        self.stateMachine.recording_finished.emit()
        return False

    def enterIdle(self):
        print("ENTER IDLE")

    def enterRunning(self):
        print("ENTER RUNNING")
        self._trial_index = 0
        self.start_protocol()

    def startRecord(self):
        print("START RECORD")
        self.protocol = self._make_protocol()
        self.protocol.run()

    def stopRecord(self):
        print("STOP RECORD")
        self._trial_index += 1
        if self._trial_index >= self.n_trials:
            self.stateMachine.experiment_finished.emit()

    def startWait(self):
        print("START WAIT")
        if self._trial_index < self.n_trials:
            self.wait_timer = QtCore.QTimer()
            self.wait_timer.setSingleShot(True)
            self.wait_timer.timeout.connect(self.start_protocol)
            self.wait_timer.start(self.inter_trial_interval)
            return
        self.stateMachine.experiment_finished.emit()
