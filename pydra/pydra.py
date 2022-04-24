from pydra.core import *
import pydra.configuration as configuration


class Pydra(PydraMain):
    """Class for main Pydra object."""

    name = "pydra"

    @staticmethod
    def run():
        pydra = Pydra._run()
        pydra.exit()

    @staticmethod
    def _run():
        """Run Pydra with the current configuration."""
        pydra = Pydra()
        pydra.setup()
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
        backend_config = configuration.BackendConfig("backend", send, recv, ipub, isub)
        backend_config.add_subscription(pydra_config, (EXIT, EVENT, REQUEST))
        pydra_config.add_receiver(backend_config)

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
            pydra_config.add_subscription(worker_config, (CONNECTION, ERROR))
            # Add subscriptions to other workers
            for other in module["worker"].subscriptions:
                other_config = worker_configs[other.name]
                worker_config.add_subscription(other_config, (EVENT, DATA, STRING, TRIGGER))

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
            saver_config.add_subscription(backend_config, (EXIT, EVENT, REQUEST))
            for worker_name in saver.workers:
                saver_config.add_subscription(worker_configs[worker_name], (EVENT, DATA, STRING, TRIGGER))
            backend_config.add_receiver(saver_config)
            saver_configs[saver.name] = saver_config

        all_configs = [pydra_config, backend_config]
        all_configs.extend(worker_configs.values())
        all_configs.extend(saver_configs.values())
        config["connections"] = dict([(cfg.name, cfg.connections) for cfg in all_configs])

        # Set the config attribute
        Pydra.config = config
        return Pydra
