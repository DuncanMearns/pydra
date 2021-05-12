from pydra import Pydra, config, ports
from pydra.modules.cameras import XIMEA


XIMEA["params"] = {
    "frame_rate": 250,
    "frame_size": (800, 800),

    "max_size": (1280, 1024)
}


config["modules"] = [XIMEA]


if __name__ == "__main__":
    Pydra.configure(config, ports)
    Pydra.run(working_dir="D:\pydra_tests", **config)
