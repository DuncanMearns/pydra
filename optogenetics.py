from pydra import Pydra, config, ports
from pydra.modules.optogenetics import OPTOGENETICS
from pydra.modules.cameras import PIKE


PIKE["params"] = {
    "frame_size": (640, 480),
    "exposure": 2,
    "gain": 5.0,

    "max_gain": 20.
}


config["modules"] = [PIKE, OPTOGENETICS]


if __name__ == "__main__":
    Pydra.configure(config, ports)
    Pydra.run(working_dir=r"D:\\DATA", **config)
