from pydra.core import *
import pydra.configuration as configuration


class Pydra(PydraMain):
    """Class for main Pydra object."""

    @staticmethod
    def run():
        pass

    @staticmethod
    def configure(modules=(), config=None, ports=None):
        config = config or configuration.config
        ports = ports or configuration.ports

        # Set/get modules
        if modules:
            config["modules"] = list(modules)
        else:
            modules = config["modules"]
        # Connect saver to pydra
        pydra_port = config["connections"]["pydra"]["port"]
        config["connections"]["saver"]["subscriptions"].append(("pydra", pydra_port, (EXIT, EVENT, LOGGED)))
        # Assign ports to workers
        for module in modules:
            worker = module["worker"]
            worker_config = {}
            pub, sub = ports.pop(0)
            worker_config["publisher"] = pub
            worker_config["port"] = sub
            config["connections"][worker.name] = worker_config
            # Add pydra subscription
            config["connections"]["pydra"]["subscriptions"].append((worker.name,
                                                                    worker_config["port"],
                                                                    (CONNECTION,)))
            # Add saver subscription
            config["connections"]["saver"]["subscriptions"].append((worker.name,
                                                                    worker_config["port"],
                                                                    (MESSAGE, LOGGED, DATA)))

        # Add connections for subscriptions
        for module in modules:
            worker = module["worker"]
            # Add subscription to pydra
            config["connections"][worker.name]["subscriptions"] = [("pydra",
                                                                    pydra_port,
                                                                    (EXIT, EVENT))]
            # Add subscriptions to other workers
            for sub in worker.subscriptions:
                port = config["connections"][sub]["port"]
                config["connections"][worker.name]["subscriptions"].append((sub,
                                                                            port,
                                                                            (EVENT, DATA, TRIGGER)))
        # Set the config attribute
        Pydra.config = config
        return Pydra
