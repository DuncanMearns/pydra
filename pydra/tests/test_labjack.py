from pydra import Pydra, config, ports
from pydra.modules.labjack import OPTOGENETICS


config["modules"] = [OPTOGENETICS]


if __name__ == "__main__":
    Pydra.configure(config, ports)
    Pydra.run(working_dir="D:\pydra_tests", **config)
