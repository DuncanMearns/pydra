from PyQt5 import QtCore

from ..base import *
from ..configuration import ZMQConfig
from ..utilities import TempCache
from ..protocol import Protocol, events
from .state_machine import Stateful


class Backend(PydraReceiver):

    name = "backend"
    subscriptions = ()

    def __init__(self, cache=50000, arr_cache=500, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cachesize = cache
        self.arr_cachesize = arr_cache
        self.caches = dict([(worker, TempCache(self.cachesize, self.arr_cachesize)) for worker in self.subscriptions])
        self.frames = {}

    def raise_error(self, error: Exception, message: str):
        raise(error)

    def recv_indexed(self, t, i, data, **kwargs):
        self.recv_data(t, i, data, **kwargs)

    def recv_array(self, t, i, a, **kwargs):
        self.recv_data(t, i, arr=a, **kwargs)

    def recv_timestamped(self, t, data, **kwargs):
        self.recv_data(t, data=data, **kwargs)

    def recv_frame(self, t, i, frame, **kwargs):
        worker = kwargs["source"]
        self.frames[worker] = frame

    def recv_data(self, t, i=None, data=None, arr=None, **kwargs):
        worker = kwargs["source"]
        self.caches[worker].append(t, i, data, arr)

    def flush(self) -> dict:
        flushed = {}
        for worker, cache in self.caches.items():
            flushed[worker] = {
                "data": cache.data,
                "array": cache.arr,
                "events": cache.events
            }
            cache.clear()
            if worker in self.frames:
                frame = self.frames.pop(worker)
                flushed[worker]["frame"] = frame
        return flushed


class PydraInterface(Stateful, QtCore.QObject):
    """Class that allows GUI to interface with Pydra. Enables Pydra protocols to be run and controlled from the GUI, and
    allows incoming data from Pydra to be broadcast to other GUI components. Has access to shared experiment state and
    associated attributes via Stateful.

    Parameters
    ----------
    pydra :
        The Pydra instance.
    """

    _new_data = QtCore.pyqtSignal()
    update_gui = QtCore.pyqtSignal(dict)

    def __init__(self, pydra):
        super().__init__()
        # Set the pydra instance
        self.pydra = pydra
        # Set shared state attributes
        self._initialize_state_attributes()
        # Protocol
        self.protocol_ = None
        # Initialize backend for receiving data from workers
        Backend.subscriptions = self.workers
        cfg = ZMQConfig("backend", "", "")
        for worker in Backend.subscriptions:
            worker_cfg = self.pydra.config.configs[worker]
            cfg.add_subscription(worker_cfg, (DATA,))
        self.backend = Backend(**cfg.connections)
        # Connect signals
        self._new_data.connect(self.poll_data)
        self.poll_timer = QtCore.QTimer()
        self.poll_timer.setInterval(30)
        self.poll_timer.setSingleShot(True)
        self.poll_timer.timeout.connect(self.poll_data)
        # Fast gui update
        self.stateMachine.gui_update.connect(self.poll_messages)
        self.stateMachine.gui_update.connect(self.check_protocol_status)
        # Handle state transitions
        self.stateMachine.ready_to_start.entered.connect(self.enterReady)
        self.stateMachine.interrupted.entered.connect(self.enterInterrupted)
        # Request data
        self.poll_data()

    def __getattr__(self, item):
        return getattr(self.pydra, item)

    @property
    def savers(self) -> list:
        return [saver.name for saver in self.pydra.savers]

    @property
    def workers(self) -> list:
        """Property for accessing all workers in Pydra config."""
        return [worker.name for worker in self.pydra.workers]

    @property
    def gui_events(self) -> list:
        """Property for accessing all defined gui_events from Pydra workers."""
        gui_events = []
        for name, worker, *etc in self.pydra.workers:
            gui_events.extend(worker.gui_events)
        return gui_events

    @property
    def trigger_threads(self):
        """Property for accessing Pydra triggers."""
        return self.pydra.triggers.threads

    def _initialize_state_attributes(self):
        # Ensure all state attributes are initialized with the params provided
        self.stateMachine.set_defaults(self.config["gui_params"])
        self.stateMachine.set_event_names(self.gui_events)
        self.stateMachine.set_targets(self.workers)
        self.stateMachine.set_triggers(self.trigger_threads)

    @QtCore.pyqtSlot()
    def poll_data(self):
        self.backend.receive_messages(1)
        data = self.backend.flush()
        if data:
            self.update_gui.emit(data)
        self.poll_timer.start()

    @QtCore.pyqtSlot()
    def poll_messages(self):
        """Polls pydra for new data."""
        self.pydra.receive_messages()

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
        # Add triggers to protocol
        start_trigger, stop_trigger = self.recording_triggers
        if start_trigger:
            protocol_list.insert(0, events.TRIGGER(start_trigger))
        if stop_trigger:
            protocol_list.insert(-1, events.TRIGGER(stop_trigger))
        # Create protocol
        protocol = Protocol.build(self.pydra, protocol_list)
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
            self.wait_timer.start(self.inter_trial_ms)
            return
        self.stateMachine.experiment_finished.emit()