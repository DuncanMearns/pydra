from ..utilities import state_descriptor

import warnings
import threading
import time
from typing import Iterable


exit_code = state_descriptor.new_type("exit_code")


class ProtocolEvent:
    """Abstract protocol event class with necessary method signatures."""

    finished = exit_code(1)
    running = exit_code(0)
    failed = exit_code(-1)

    def __init__(self):
        self.finished()

    def update(self):
        pass

    def reset(self):
        pass


class PauseEvent(ProtocolEvent):
    """Pause event. Waits until t seconds have passed. Waits forever if t is negative."""

    def __init__(self, t: float):
        super().__init__()
        self.t = t
        self.started = False

    def start(self):
        self.t0 = time.perf_counter()
        self.running()
        self.started = True

    def update(self):
        if not self.started:
            self.start()
        if self.t < 0:
            self.running()
        elif (time.perf_counter() - self.t0) >= self.t:
            self.finished()

    def reset(self):
        self.started = False

    def __repr__(self):
        return f"{self.__class__.__name__}(t={self.t})"


class TriggerEvent(PauseEvent):
    """Trigger event. Checks whether trigger has been received via check method until timeout time has elapsed."""

    def __init__(self, trigger_flag: threading.Event, reset_flag, one_shot: bool = False, timeout: float = -1):
        super().__init__(timeout)
        self.trigger_flag = trigger_flag
        self.reset_flag = reset_flag
        self.one_shot = one_shot

    def check(self):
        if self.trigger_flag.is_set():
            self.finished()
            if not self.one_shot:
                self.reset()

    def update(self):
        super().update()
        if self.finished:  # timed out
            self.failed()
            return
        self.check()

    def reset(self):
        self.reset_flag.set()
        super().reset()


class PydraEvent(ProtocolEvent):
    """Sends an event through pydra."""

    def __init__(self, pydra, event: str, event_kw: dict = None):
        super().__init__()
        self.pydra = pydra
        self.event = event
        self.event_kw = event_kw if event_kw else {}

    def update(self):
        self.pydra.send_event(self.event, **self.event_kw)
        self.finished()

    def __repr__(self):
        return f"{self.__class__.__name__}(pydra, {self.event}, {self.event_kw})"


class ProtocolThread(threading.Thread):
    """Thread class for running through a list of ProtocolEvent objects.

    Parameters
    ----------
    events : iterable of ProtocolEvent
        Sequence of ProtocolEvent objects in the protocol.
    """

    def __init__(self, events=()):
        super().__init__()
        self.events = events
        # Flags
        self.exit_flag = threading.Event()
        self.next_flag = threading.Event()
        # Internal attributes
        self.current_event = None  # current ProtocolEvent object

    @property
    def events(self):
        """Property containing a list of events in the protocol."""
        return self._event_queue

    @events.setter
    def events(self, event_queue):
        """Setter for list of protocol events."""
        if self.is_alive():
            warnings.warn("Cannot modify a running protocol.")
        else:
            self._event_queue = list(event_queue)  # make a copy of the event queue

    def abort(self):
        """Aborts the current protocol."""
        self.exit()

    def exit(self):
        """Sets the exit flag to true."""
        self.exit_flag.set()

    def next(self):
        """If there are still events in the protocol, pops the next one from the list and sets it as the current event,
        otherwise ends the protocol."""
        if len(self.events):
            self.current_event = self.events.pop(0)
            self.current_event.reset()
        else:
            self.exit()

    def run(self) -> None:
        """Run method for the ProtocolThread."""
        self.next()  # initialize the current event
        while not self.exit_flag.is_set():
            if self.next_flag.is_set():  # check if next flag is set
                self.next()
                self.next_flag.clear()
            self.current_event.update()  # update current event
            if self.current_event.finished:  # move onto next event if current finished
                self.next()
                continue
            if self.current_event.failed:  # event failed, abort protocol
                self.abort()
            time.sleep(0.01)


class Protocol:
    """Class for building and running protocols."""

    def __init__(self):
        self.event_queue = []
        self.thread = None

    def run(self):
        # Check protocol is not already running
        if self.thread and self.thread.is_alive():
            warnings.warn("Cannot re-enter protocol thread.")
            return
        # Start protocol
        self.thread = ProtocolThread(self.event_queue)
        self.thread.start()

    def next(self):
        self.thread.next_flag.set()

    def interrupt(self):
        self.thread.exit()
        self.thread.join()

    def wait(self):
        self.thread.join()

    def restart(self):
        self.interrupt()
        self.run()

    def addPause(self, t: float):
        """Add a pause of t seconds to the protocol."""
        self.event_queue.append(PauseEvent(t))

    def addEvent(self, pydra, name: str, kw: dict = None):
        """Add a pydra event to the protocol."""
        self.event_queue.append(PydraEvent(pydra, name, kw))

    def addFreerun(self):
        """Add an infinite pause to the protocol."""
        self.event_queue.append(PauseEvent(-1))

    def addTrigger(self, trigger_flag: threading.Event, reset_flag: threading.Event, one_shot: bool=False, t: float=-1):
        """Add a trigger to the protocol with a timeout of t second."""
        self.event_queue.append(TriggerEvent(trigger_flag, reset_flag, one_shot, t))

    def is_running(self):
        try:
            return self.thread.is_alive()
        except AttributeError:
            return False

    @staticmethod
    def build(pydra, protocol_events):
        return build_protocol(pydra, protocol_events)


def build_protocol(pydra, protocol_events: Iterable) -> Protocol:
    protocol = Protocol()
    for event in protocol_events:
        event.add(pydra, protocol)
    return protocol


Protocol.build = staticmethod(build_protocol)
