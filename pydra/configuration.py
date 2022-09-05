import typing
from collections import namedtuple

from .utils.config import ZMQConfig, port_manager
from .modules import PydraModule
from .messaging import *


class ConnectionManager:

    def __init__(self, ports):
        self.ports = ports
        # Configs
        self._master_config = None
        self._worker_configs = {}
        # Subscription queue (if trying to add a subscription before config has been initialized)
        self._subscription_queue = []

    @property
    def configs(self):
        all_configs = {"pydra": self._master_config}
        all_configs.update(self._worker_configs)
        return all_configs

    @property
    def connections(self):
        return dict([(name, config.connections) for (name, config) in self.configs.items()])

    @property
    def master_config(self):
        if self._master_config:
            return self._master_config
        raise AttributeError("Must add pydra master config.")

    def add_master(self, pub_sub: tuple = None):
        pub, sub = pub_sub or self.ports.next()
        self._master_config = ZMQConfig("pydra", pub, sub)

    def add_worker(self, name: str, subscriptions: typing.Iterable[str] = (), pub_sub: tuple = None):
        """Add worker to configs."""
        # Get pub-sub ports
        pub, sub = pub_sub or self.ports.next()
        # Initialize config
        config = ZMQConfig(name, pub, sub)
        # Add subscription to pydra
        config.add_subscription(self.master_config, (EXIT, EVENT))
        # Subscribe pydra to worker
        self.master_config.add_subscription(config, (CONNECTION, ERROR))
        # Add subscriptions to other workers
        for subscription in subscriptions:
            try:
                other_config = self.configs[subscription]
                config.add_subscription(other_config, (EVENT, DATA, STRING, TRIGGER))
            except KeyError:
                # Add to queue
                self._subscription_queue.append((name, subscription))
        # Add to worker configs
        self._worker_configs[name] = config

    def verify_connections(self):
        """Ensures all queued connections are added to configs."""
        while True:
            try:
                subscriber, subscription = self._subscription_queue.pop()
                self.configs[subscriber].add_subscription(self.configs[subscription], (EVENT, DATA, STRING, TRIGGER))
            except IndexError:
                break


worker_tuple = namedtuple("worker_tuple", ("name", "worker_cls", "args", "kwargs"))


class Configuration:

    def __init__(self, *,
                 modules=None,
                 triggers=None,
                 saver_params=None,
                 gui_params=None,
                 auto_config=True,
                 ports=port_manager):
        self.modules = modules
        self.triggers = triggers
        self.saver_params = saver_params or {}
        self.gui_params = gui_params
        # Connection manager
        self.connection_manager = ConnectionManager(ports)
        if auto_config:
            self.auto_configure()

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
        from pydra.gui.default_params import default_params
        self._gui_params = default_params
        if params:
            self._gui_params.update(params)

    @property
    def connections(self) -> dict:
        return self.connection_manager.connections

    def auto_configure(self):
        """Auto configure connections."""
        self.connection_manager.add_master()
        for worker in self.workers:
            name = worker.name
            worker_cls = worker.worker_cls
            self.connection_manager.add_worker(name, worker_cls.subscriptions)
        for saver in self.savers:
            name = saver.name
            saver_cls = saver.worker_cls
            self.connection_manager.add_worker(name, saver_cls.subscriptions)
        self.connection_manager.verify_connections()

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
                msg = msg + f"\tsaves: " + ", ".join([worker for worker in saver.worker_cls.subscriptions])
                out = out + msg + "\n"
        return out
