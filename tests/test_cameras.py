from pydra import Pydra, ports, config
from pydra.modules.cameras import PIKE
from pydra.core import Acquisition


PIKE["worker"] = Acquisition


config["modules"] = [PIKE]


if __name__ == "__main__":
    config = Pydra.configure(config, ports)
    pydra = Pydra.run(working_dir="D:\pydra_tests", **config)
