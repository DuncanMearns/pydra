import zmq
import threading
from abc import ABC, abstractmethod


__all__ = ["TriggerThread", "Trigger", "ZMQTrigger"]


class _TriggerBase(ABC):
    """Abstract base class for Trigger. Only for type checking."""

    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def check(self) -> bool:
        """Check for trigger."""
        pass

    @abstractmethod
    def reset(self) -> None:
        pass


class Trigger(_TriggerBase):
    """Base Trigger object with all abstract methods implements with proper call signatures for context management."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __enter__(self) -> _TriggerBase:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def check(self) -> bool:
        """Check for trigger."""
        return False

    def reset(self) -> None:
        pass


class ZMQTrigger(Trigger):
    """Class for receiving triggers over ZMQ.

    Parameters
    ----------
    port : str
        The port over which to listen for triggers in a PUB/SUB pattern.
    """

    def __init__(self, port, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.port = port

    def __enter__(self):
        self.ctx = zmq.Context.instance()
        self.sock = self.ctx.socket(zmq.SUB)
        self.sock.setsockopt(zmq.SUBSCRIBE, b"")
        self.sock.connect(self.port)
        return self

    def check(self) -> bool:
        try:
            if self.sock.poll(0):
                self.sock.recv()
                print(f"zmq trigger from {self.port} received")
                return True
        except zmq.error.ZMQError as e:
            print(e)
        return False

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sock.close()


class TriggerThread(threading.Thread):
    """Implements context manager for Trigger objects in a thread."""

    def __init__(self, trigger: Trigger):
        super().__init__()
        self.trigger = trigger
        self.event_flag = threading.Event()
        self.reset_flag = threading.Event()
        self.exit_flag = threading.Event()

    def terminate(self):
        self.exit_flag.set()

    def reset(self):
        self.reset_flag.set()

    def run(self) -> None:
        with self.trigger as trigger:  # open trigger in context manager
            while not self.exit_flag.is_set():  # run event loop while exit flag is not set
                if self.reset_flag.is_set():  # check if trigger needs to be reset
                    self.reset_flag.clear()  # clear reset flag
                    self.event_flag.clear()  # clear event flag
                    trigger.reset()  # reset trigger
                if trigger.check():  # check is trigger fired
                    self.event_flag.set()  # set event flag
