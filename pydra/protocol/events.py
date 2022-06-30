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
    trig: object

    def add(self, pydra, protocol: Protocol):
        pass


class FREERUN(PROTOCOL_EVENT):

    def add(self, pydra, protocol: Protocol):
        protocol.addFreerun()

    def __repr__(self):
        return "FREERUN()"
