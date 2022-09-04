from dataclasses import dataclass, field
import typing
from collections import namedtuple
from .modules import PydraModule
from .classes import Worker, Saver
from .messaging import *
from .gui.default_params import default_params


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
class ZMQConfig:
    name: str

    @property
    def connections(self):
        connection_dict = self.__dict__.copy()
        connection_dict.pop("name")
        return connection_dict


@dataclass
class SenderConfig(ZMQConfig):
    sender: str
    recv: str


@dataclass
class PublisherConfig(ZMQConfig):
    publisher: str
    sub: str


@dataclass
class ReceiverConfig(ZMQConfig):
    receivers: typing.List = field(default_factory=lambda: [])

    def add_receiver(self, sender: SenderConfig):
        self.receivers.append((sender.name, sender.recv))


@dataclass
class SubscriberConfig:
    subscriptions: typing.List = field(default_factory=lambda: [])

    def add_subscription(self, publisher: PublisherConfig, messages: tuple):
        self.subscriptions.append((publisher.name, publisher.sub, messages))


PydraConfig = dataclass(type("PydraConfig", (SubscriberConfig, ReceiverConfig, PublisherConfig), {}))
BackendConfig = dataclass(type("BackendConfig", (SubscriberConfig, ReceiverConfig, PublisherConfig, SenderConfig), {}))
WorkerConfig = dataclass(type("WorkerConfig", (SubscriberConfig, PublisherConfig), {}))
SaverConfig = dataclass(type("SaverConfig", (SubscriberConfig, SenderConfig), {}))


worker_tuple = namedtuple("worker_tuple", ("name", "worker_cls", "args", "kwargs"))


class Configuration:

    def __init__(self, *,
                 modules=None,
                 triggers=None,
                 saver_params=None,
                 gui_params=None,
                 _connections=None,
                 _public_ports=ports,
                 _private_ports=_ports):
        self.modules = modules
        self.triggers = triggers
        self.saver_params = saver_params or {}
        self.gui_params = gui_params
        if _connections:
            self.connections = _connections
        else:
            # AUTOMATIC CONFIGURATION
            self.add_connections(_public_ports, _private_ports)

    def __getitem__(self, item):
        try:
            return getattr(self, item)
        except AttributeError:
            raise KeyError(f"Configuration has no {item} key.")

    @property
    def modules(self) -> list:
        return list(self._modules)

    @modules.setter
    def modules(self, module_list: typing.Iterable[typing.Union[PydraModule, dict]]):
        self._modules = []
        if module_list:
            for module in module_list:
                if isinstance(module, dict):
                    module = PydraModule(**module)
                self._modules.append(module)
        self._modules = tuple(self._modules)

    @property
    def workers(self) -> typing.List[worker_tuple]:
        """Read-only property."""
        return [worker_tuple(module.name,
                             module.worker,
                             module.worker_args,
                             module.worker_kwargs) for module in self.modules]

    @property
    def savers(self) -> typing.List[worker_tuple]:
        """Read-only property."""
        saver_set = set(saver for module in self._modules if (saver := module.saver))
        saver_tuples = []
        for saver in saver_set:
            name = saver.name
            params = self.saver_params.get(name, {})
            saver_tuples.append(worker_tuple(name, saver, (), params))
        return saver_tuples

    @property
    def triggers(self) -> dict:
        return self._triggers

    @triggers.setter
    def triggers(self, trigger_dict: typing.Mapping):
        self._triggers = {}
        if trigger_dict:
            self._triggers.update(trigger_dict)

    @property
    def gui_params(self) -> dict:
        return self._gui_params

    @gui_params.setter
    def gui_params(self, params: typing.Mapping):
        self._gui_params = default_params
        if params:
            self._gui_params.update(params)

    @property
    def connections(self) -> dict:
        return self._connections

    @connections.setter
    def connections(self, _connections: typing.Mapping):
        self._connections = {}
        if _connections:
            self._connections.update(_connections)

    def add_connections(self, public: PortManager = None, private: PortManager = None):
        """Generates a configuration dictionary (stored in config class attribute).

        Parameters
        ----------
            public : configuration.PortManager (optional)
                Ports to use for frontend zmq connections.
            private : configuration.PortManager (optional)
                Ports to use for backend zmq connections.
        """

        public = public or ports
        private = private or _ports

        # Get backend ports
        pub, sub = private.next()
        # send, recv = private.next()
        # bpub, bsub = private.next()

        # Initialize backend configuration
        pydra_config = PydraConfig("pydra", pub, sub)
        # backend_config = BackendConfig("backend", send, recv, bpub, bsub)
        # backend_config.add_subscription(pydra_config, (EXIT, EVENT, REQUEST))
        # pydra_config.add_receiver(backend_config)

        # Initialize worker configuration
        worker_configs = {}
        for worker in self.workers:
            name = worker.name
            pub, sub = public.next()
            worker_config = WorkerConfig(name, pub, sub)
            # Add worker to configs
            worker_configs[name] = worker_config

        # Handle worker subscriptions
        for worker in self.workers:
            name = worker.name
            worker_cls = worker.worker_cls
            worker_config = worker_configs[name]
            # Add subscription to pydra
            worker_config.add_subscription(pydra_config, (EXIT, EVENT))
            # Add to pydra subscriptions
            pydra_config.add_subscription(worker_config, (CONNECTION, ERROR))
            # Add subscriptions to other workers
            for other in worker_cls.subscriptions:
                other_config = worker_configs[other.name]
                worker_config.add_subscription(other_config, (EVENT, DATA, STRING, TRIGGER))
            worker_cls.connections = worker_config.connections

        # Configure savers
        saver_configs = {}
        for saver in self.savers:
            saver_cls = saver.worker_cls
            send, recv = private.next()
            saver_config = SaverConfig(saver.name, send, recv)
            saver_config.add_subscription(pydra_config, (EXIT, EVENT, REQUEST))
            for worker_name in saver_cls.subscriptions:
                saver_config.add_subscription(worker_configs[worker_name], (EVENT, DATA, STRING, TRIGGER))
            pydra_config.add_receiver(saver_config)
            saver_configs[saver.name] = saver_config
            saver_cls.connections = saver_config.connections

        # all_configs = [pydra_config, backend_config]
        all_configs = [pydra_config]
        all_configs.extend(worker_configs.values())
        all_configs.extend(saver_configs.values())
        self.connections = dict([(cfg.name, cfg.connections) for cfg in all_configs])

    def __str__(self):
        out = "\n" \
              "===========\n" \
              "CONNECTIONS\n" \
              "===========\n\n"
        for obj, d in self.connections.items():
            msg = f"*{obj}*\n"
            msg = msg + "\tports:\n"
            if 'publisher' in d:
                pub = d['publisher']
                sub = d['sub']
                msg = msg + f"\t\tpub-sub: {pub}, {sub}\n"
            if 'sender' in d:
                send = d['sender']
                recv = d['recv']
                msg = msg + f"\t\tsend-recv: {send}, {recv}\n"
            if 'subscriptions' in d and len(d['subscriptions']):
                msg = msg + "\tsubscribes to:\n"
                for (name, port, msg_types) in d['subscriptions']:
                    msg = msg + f"\t\t{name} " + f"{msg_types}\n"
            if 'receivers' in d and len(d['receivers']):
                msg = msg + "\treceives from:\n"
                msg = msg + "\t\t" + ", ".join([name for (name, port) in d['receivers']]) + "\n"
            out = out + msg + "\n"
        if len(self.modules):
            out = out + "=======\n" \
                        "MODULES\n" \
                        "=======\n\n"
            for mod in self.modules:
                worker = mod["worker"]
                msg = f"*{worker.name}*\n"
                if mod.widget:
                    msg = msg + "\twidget: " + mod['widget'].__name__ + "\n"
                if mod.plotter:
                    msg = msg + "\tplotter: " + mod['plotter'].__name__ + "\n"
                if mod.worker_kwargs:
                    msg = msg + "\tparams: {\n"
                    for param, val in mod.worker_kwargs.items():
                        msg = msg + f"\t\t{param}: {val}"
                    msg = msg + "\t}\n"
                if len(worker.gui_events):
                    msg = msg + "\tgui events: " + ", ".join([event for event in worker.gui_events]) + "\n"
                out = out + msg + "\n"
        if len(self.savers):
            out = out + "======\n" \
                        "SAVERS\n" \
                        "======\n\n"
            for saver in self.savers:
                msg = f"*{saver.name}*\n"
                msg = msg + f"\tsaves: " + ", ".join([worker for worker in saver.workers])
                out = out + msg + "\n"
        return out
