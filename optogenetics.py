from pydra import Pydra, config, ports
from pydra.modules.optogenetics import OPTOGENETICS
from pydra.modules.cameras import XIMEA


XIMEA["params"] = {
    "frame_size": (368, 312),
    "frame_rate": 250.,
    "exposure": 0.5,
    "gain": 0.,

    "min_size": (250, 250),
    "max_size": (1280, 1024),
    "min_gain": 0.,
    "max_gain": 20.,
    "min_exposure": 0.01,
    "max_exposure": 100.,
}


config["modules"] = [XIMEA, OPTOGENETICS]


if __name__ == "__main__":
    Pydra.configure(config, ports)
    Pydra.run(working_dir=r"D:\\DATA", **config)
