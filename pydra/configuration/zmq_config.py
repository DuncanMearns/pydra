"""
Module for handling tcp addresses and zmq configurations.
"""
import typing
from dataclasses import dataclass, field


__all__ = ("PortManager", "port_manager", "ZMQConfig")


class Port:

    def __init__(self, val):
        self.__val = val

    @property
    def val(self):
        return self.__val

    @property
    def bind(self):
        return f"tcp://*:{self.val}"

    @property
    def connect(self):
        return f"tcp://localhost:{self.val}"

    def __iter__(self):
        return iter((self.bind, self.connect))


class PortManager:

    def __init__(self, start):
        self.current = start

    def next(self):
        port = Port(self.current)
        self.current += 1
        return port


port_manager = PortManager(5555)


@dataclass
class ZMQConfig:
    name: str
    publisher: str
    sub: str
    subscriptions: typing.List = field(default_factory=lambda: [])

    @property
    def connections(self):
        connection_dict = self.__dict__.copy()
        connection_dict.pop("name")
        return connection_dict

    def add_subscription(self, publisher, messages: tuple):
        self.subscriptions.append((publisher.name, publisher.sub, messages))
