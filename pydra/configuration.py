from dataclasses import dataclass, field
from typing import List


class Port:

    def __init__(self, val):
        self.__val = val

    @property
    def val(self):
        return self.__val

    @val.setter
    def val(self, val):
        raise ValueError("Cannot change the value of a port.")

    @property
    def write(self):
        return f"tcp://*:{self.val}"

    @property
    def read(self):
        return f"tcp://localhost:{self.val}"

    def __iter__(self):
        return iter((self.write, self.read))


class PortManager:

    def __init__(self, start):
        self.current = start

    def next(self):
        port = Port(self.current)
        self.current += 1
        return port


ports = PortManager(5555)
_ports = PortManager(6000)


@dataclass
class Configuration:
    name: str

    @property
    def connections(self):
        connection_dict = self.__dict__.copy()
        connection_dict.pop("name")
        return connection_dict


@dataclass
class SenderConfig(Configuration):
    sender: str
    recv: str


@dataclass
class PublisherConfig(Configuration):
    publisher: str
    sub: str


@dataclass
class ReceiverConfig(Configuration):
    receivers: List = field(default_factory=lambda: [])

    def add_receiver(self, sender: SenderConfig):
        self.receivers.append((sender.name, sender.recv))


@dataclass
class SubscriberConfig:
    subscriptions: List = field(default_factory=lambda: [])

    def add_subscription(self, publisher: PublisherConfig, messages: tuple):
        self.subscriptions.append((publisher.name, publisher.sub, messages))


PydraConfig = dataclass(type("PydraConfig", (SubscriberConfig, ReceiverConfig, PublisherConfig), {}))
BackendConfig = dataclass(type("BackendConfig", (SubscriberConfig, ReceiverConfig, PublisherConfig, SenderConfig), {}))
WorkerConfig = dataclass(type("WorkerConfig", (SubscriberConfig, PublisherConfig), {}))
SaverConfig = dataclass(type("SaverConfig", (SubscriberConfig, SenderConfig), {}))


config = {

    "connections": {},

    "modules": [],

    "savers": [],

    "trigger": None,

    "gui_params": {
        "directory": "",
        "filename": "",
        "n_trial_digits": 3,
        "n_trials": 1,
        "inter_trial_time": 1,
        "inter_trial_unit": "s"
    }

}
