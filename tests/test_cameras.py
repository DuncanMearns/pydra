from pydra import Pydra, ports, config
from pydra.modules.cameras.ximea import XIMEA


XIMEA["params"] = {
    "frame_size": (640, 512),
    "min_frame_rate": 50.,
    "frame_rate": 200.,
    "max_exposure": 20
}


config["modules"] = [XIMEA]


if __name__ == "__main__":
    config = Pydra.configure(config, ports)
    pydra = Pydra.run(working_dir="D:\pydra_tests", **config)
