from .protocol import Protocol
from .triggers import *
from . import events
import typing


def build_protocol(pydra, protocol_events: typing.List[events.PROTOCOL_EVENT]) -> Protocol:
    protocol = Protocol()
    for event in protocol_events:
        event.add(pydra, protocol)
    return protocol


Protocol.build = staticmethod(build_protocol)
