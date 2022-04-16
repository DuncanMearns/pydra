from pydra.core import *
import pydra.configuration as configuration


class Pydra(PydraMain):
    """Class for main Pydra object."""

    @staticmethod
    def run():
        pydra = Pydra._run()
        pydra.exit()

    @staticmethod
    def _run():
        """Run Pydra with the current configuration."""
        pydra = Pydra()
        pydra.start_savers()
        for module in pydra.config["modules"]:
            worker = module["worker"]
            params = module.get("params", {})
            threaded = module.get("threaded", False)
            pydra.start_worker(worker, params, as_thread=threaded)
        pydra.network_test()
        return pydra

    @staticmethod
    def configure(modules=(),
                  savers=(),
                  config: dict = None,
                  public: configuration.PortManager = None,
                  private: configuration.PortManager = None):

        config = config or configuration.config
        public = public or configuration.ports
        private = private or configuration._ports

        # Get backend ports
        pub, sub = private.next()
        send, recv = private.next()
        ipub, isub = private.next()

        # Initialize backend configuration
        pydra_config = configuration.PydraConfig("pydra", pub, sub)
        interface_config = configuration.InterfaceConfig("interface", send, recv, ipub, isub)
        interface_config.add_subscription(pydra_config, (EXIT, EVENT, QUERY))
        pydra_config.add_receiver(interface_config)

        # Set/get modules
        if modules:
            config["modules"] = list(modules)
        else:
            modules = config["modules"]

        # Initialize worker configuration
        worker_configs = {}
        for module in modules:
            name = module["worker"].name
            pub, sub = public.next()
            worker_config = configuration.WorkerConfig(name, pub, sub)
            # Add worker to configs
            worker_configs[name] = worker_config

        # Handle worker subscriptions
        for module in modules:
            name = module["worker"].name
            worker_config = worker_configs[name]
            # Add subscription to pydra
            worker_config.add_subscription(pydra_config, (EXIT, EVENT))
            # Add to pydra and interface subscriptions
            pydra_config.add_subscription(worker_config, (CONNECTION,))
            interface_config.add_subscription(worker_config, (MESSAGE, DATA))
            # Add subscriptions to other workers
            for other in module["worker"].subscriptions:
                other_config = worker_configs[other.name]
                worker_config.add_subscription(other_config, (EVENT, DATA, TRIGGER))

        # Set/get savers
        if savers:
            config["savers"] = list(savers)
        else:
            savers = config["savers"]

        # Configure savers
        saver_configs = {}
        for saver in savers:
            send, recv = private.next()
            saver_config = configuration.SaverConfig(saver.name, send, recv)
            saver_config.add_subscription(interface_config, (EXIT, EVENT))
            for worker_name in saver.workers:
                saver_config.add_subscription(worker_configs[worker_name], (DATA,))
            interface_config.add_receiver(saver_config)
            saver_configs[saver.name] = saver_config

        all_configs = [pydra_config, interface_config]
        all_configs.extend(worker_configs.values())
        all_configs.extend(saver_configs.values())
        config["connections"] = dict([(cfg.name, cfg.connections) for cfg in all_configs])

        # Set the config attribute
        Pydra.config = config
        return Pydra
