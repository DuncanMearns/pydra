import warnings
from threading import Thread
import queue
import time
from ..utils.state import state_descriptor


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


class Pause(ProtocolEvent):
    """Pause event. Waits until t seconds have passed. Waits forever if t is negative."""

    def __init__(self, t):
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


class Trigger(Pause):
    """Trigger event. Checks whether trigger has been received via check method until timeout time has elapsed."""

    def __init__(self, timeout=-1):
        super().__init__(timeout)
        self.triggered = False

    def check(self):
        self.finished()

    def update(self):
        super().update()
        if self.finished:  # timed out
            self.failed()
            return
        self.check()

    def reset(self):
        self.triggered = False


class Event(ProtocolEvent):
    """Sends an event through pydra."""

    def __init__(self, pydra, event, event_kw=None):
        super().__init__()
        self.pydra = pydra
        self.event = event
        self.event_kw = event_kw if event_kw else {}

    def update(self):
        self.pydra.send_event(self.event, **self.event_kw)
        self.finished()


class ProtocolThread(Thread):
    """Thread class for running through a list of ProtocolEvent objects."""

    def __init__(self, msg_q, events=()):
        super().__init__()
        self.msg_q = msg_q
        self.events = events
        # Internal attributes
        self.flag = False
        self.current_event = None
        self.callback = {
            0: self.abort,
            1: self.next
        }

    @property
    def events(self):
        return self._event_queue

    @events.setter
    def events(self, event_queue):
        if self.is_alive():
            warnings.warn("Cannot modify a running protocol.")
        else:
            self._event_queue = list(event_queue)  # make a copy of the event queue

    def abort(self):
        self.exit()

    def exit(self):
        self.flag = True

    def next(self):
        if len(self.events):
            self.current_event = self.events.pop(0)
            self.current_event.reset()
        else:
            self.exit()

    def run(self) -> None:
        self.next()  # initialize the current event
        while not self.flag:
            try:
                # check for messages in queue
                msg = self.msg_q.get_nowait()
                # call method corresponding to code
                self.callback.get(msg, lambda: 0)()
            except queue.Empty:
                self.current_event.update()  # update current event
                if self.current_event.finished:  # move onto next event if current finished
                    self.next()
                    continue
                if self.current_event.failed:  # event failed, abort protocol
                    self.abort()


class Protocol:
    """Class for building and running protocols."""

    def __init__(self):
        self.msg_q = queue.Queue()
        self.event_queue = []
        self.thread = None

    def run(self):
        # Check protocol is not already running
        if self.thread and self.thread.is_alive():
            warnings.warn("Cannot re-enter protocol thread.")
            return
        # Clear message queue
        while not self.msg_q.empty():
            self.msg_q.get_nowait()
        # Start protocol
        self.thread = ProtocolThread(self.msg_q, self.event_queue)
        self.thread.start()

    def next(self):
        self.msg_q.put(1)

    def interrupt(self):
        self.msg_q.put(0)
        self.thread.join()

    def wait(self):
        self.thread.join()

    def restart(self):
        self.interrupt()
        self.run()

    def addPause(self, t):
        self.event_queue.append(Pause(t))

    def addEvent(self, pydra, name, kw=None):
        self.event_queue.append(Event(pydra, name, kw))

    def addFreerun(self):
        self.event_queue.append(Pause(-1))
