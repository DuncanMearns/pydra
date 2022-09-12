from ..base import *
from ..protocol import *
from .zmq_config import *
from .pydra_module import *

from typing import Iterable, Mapping, Any
from collections import namedtuple


__all__ = ["Configuration", "PydraModule", "pydra_tuple", "ZMQConfig"]


pydra_tuple = namedtuple("pydra_tuple", ("name", "cls", "args", "kwargs"))


class Configuration:
    """Configuration class for pydra.

    Parameters
    ----------
    modules : iterable of PydraModule
        PydraModules to load.
    triggers : iterable of Triggers
        Available triggers.
    saver_params : dict
        Dictionaries for initializing each Saver.
    gui_params : mapping
        Dictionary of params passed to GUI. See gui package for defaults.
    auto_config : bool
        Whether to configure zmq connections automatically (recommended).
    ports : PortManager
        Ports to use for autoconfiguration.
    configs : iterable of ZMQConfigs
        ZMQ Configurations for each PydraObject in the network if not autoconfigured (advanced).
    """

    def __init__(self, *,
                 modules: Iterable[PydraModule] = None,
                 triggers: Mapping[str, Trigger] = None,
                 saver_params: Mapping[str, dict] = None,
                 gui_params: Mapping[str, Any] = None,
                 auto_config: bool = True,
                 ports: PortManager = port_manager,
                 configs: Mapping[str, ZMQConfig] = None):
        self.modules = modules
        self.triggers = triggers
        self.saver_params = saver_params or {}
        self.gui_params = gui_params
        # Connection manager
        self.configs = {}
        if auto_config:
            self.configs = self.auto_configure(ports)
        elif configs:
            self.configs = configs

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

    def get_module(self, name):
        """Returns the PydraModule in the configuration with the corresponding name."""
        matches = list(filter(lambda x: x.name == name, self.modules))
        if matches:
            return matches.pop()
        else:
            raise ValueError(f"{name} is not in modules")

    @property
    def workers(self) -> typing.List[pydra_tuple]:
        """Read-only property."""
        tuples = []
        for module in self.modules:
            name = module.name
            worker = module.worker
            args = module.worker_args
            kw = module.worker_kwargs
            connections = self.connections.get(name, {})
            kw.update(connections)
            tuples.append(pydra_tuple(name, worker, args, kw))
        return tuples

    @property
    def savers(self) -> typing.List[pydra_tuple]:
        """Read-only property."""
        saver_set = set(saver for module in self._modules if (saver := module.saver))
        saver_tuples = []
        for saver in saver_set:
            name = saver.name
            params = self.saver_params.get(name, {})
            connections = self.connections.get(name, {})
            params.update(connections)
            saver_tuples.append(pydra_tuple(name, saver, (), params))
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
        """Returns a dictionary containing all connections in the network."""
        return dict([(name, cfg.connections) for name, cfg in self.configs.items()])

    def auto_configure(self, ports: PortManager):
        """Auto configure connections (default and recommended behavior)."""
        # Pydra config
        pub, sub = ports.next()
        pydra_cfg = ZMQConfig(name="pydra", publisher=pub, sub=sub)
        # Configs
        configs = {"pydra": pydra_cfg}
        worker_subscriptions = []  # keep track of subscriptions to add after all configs initialized
        for name, worker, *etc in self.workers:
            pub, sub = ports.next()
            cfg = ZMQConfig(name=name, publisher=pub, sub=sub)
            cfg.add_subscription(pydra_cfg, (EXIT, EVENT, TRIGGER))
            pydra_cfg.add_subscription(cfg, (CONNECTION, ERROR))
            configs[name] = cfg
            worker_subscriptions.append((name, worker.subscriptions))
        # Finish worker configs
        for name, subs in worker_subscriptions:
            configs[name].add_subscription(configs[name], (EVENT, DATA, STRING, TRIGGER))
        # Saver configs
        for name, saver, *etc in self.savers:
            pub, sub = ports.next()
            cfg = ZMQConfig(name=name, publisher=pub, sub=sub)
            cfg.add_subscription(pydra_cfg, (EXIT, EVENT, TRIGGER))
            pydra_cfg.add_subscription(cfg, (CONNECTION, ERROR))
            for worker in saver.subscriptions:
                cfg.add_subscription(configs[worker], (DATA,))
            configs[name] = cfg
        return configs

    def __str__(self):
        out = "\n" + "-" * 50 + "\n"

        out = out + "===========\n" \
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
                    msg = msg + f"\t\t{name} " + f"{list(msg_types)}\n"
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
            for name, saver, *etc in self.savers:
                msg = f"*{name}*\n"
                msg = msg + f"\tsaves: " + ", ".join([worker for worker in saver.subscriptions])
                out = out + msg + "\n"
        if len(self.triggers):
            out = out + "========\n" \
                        "TRIGGERS\n" \
                        "========\n\n" \
                        f"{','.join(self.triggers.keys())}\n"
        out = out + "\n" + "-" * 50 + "\n"
        return out
