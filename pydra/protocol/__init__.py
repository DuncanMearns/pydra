import typing
from .protocol import Protocol
from .triggers import Trigger, TriggerThread
from . import events


def build_protocol(pydra, protocol_events: typing.List[events.PROTOCOL_EVENT]) -> Protocol:
    protocol = Protocol()
    for event in protocol_events:
        event.add(pydra, protocol)
    return protocol
