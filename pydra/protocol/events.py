from .protocol import Protocol

from dataclasses import dataclass
from abc import ABC, abstractmethod


class PROTOCOL_EVENT(ABC):

    @abstractmethod
    def add(self, pydra, protocol: Protocol):
        pass


@dataclass
class EVENT(PROTOCOL_EVENT):
    name: str
    kw : dict = None

    def add(self, pydra, protocol: Protocol):
        protocol.addEvent(pydra, self.name, self.kw)


@dataclass
class PAUSE(PROTOCOL_EVENT):
    time: float

    def add(self, pydra, protocol: Protocol):
        protocol.addPause(self.time)


@dataclass
class TRIGGER(PROTOCOL_EVENT):
    trig: str

    def add(self, pydra, protocol: Protocol):
        trigger_thread = pydra.triggers[self.trig]
        protocol.addTrigger(trigger_thread.event_flag, trigger_thread.reset_flag)


class FREERUN(PROTOCOL_EVENT):

    def add(self, pydra, protocol: Protocol):
        protocol.addFreerun()

    def __repr__(self):
        return "FREERUN()"
