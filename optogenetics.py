from pydra import Pydra, config, ports
from pydra.modules.optogenetics import OPTOGENETICS
from pydra.modules.cameras.ximea import XIMEA
from pydra.modules.tracking.tail_tracker import TAIL_TRACKER, TailOverlay


XIMEA["params"] = {

    "frame_size": (300, 300),
    "frame_rate": 200.,
    "exposure": 2000,
    "gain": 1.,

    "min_size": (250, 250),
    "max_size": (1280, 1024),
    "min_gain": 0.,
    "max_gain": 20.,
    "min_exposure": 0.001,
    "max_exposure": 10.}


# XIMEA["plotter"] = TailOverlay


# TAIL_TRACKER["worker"].subscriptions = ("ximea",)
# TAIL_TRACKER["params"]["acquisition_worker"] = "ximea"


config["modules"] = [XIMEA, OPTOGENETICS]#, TAIL_TRACKER]


# config["modules"] = [OPTOGENETICS]


if __name__ == "__main__":
    Pydra.configure(config, ports)
    Pydra.run(working_dir=r"D:\\DATA\\Orsi_opto", **config)

### Changes made: we set Pydra to process ms instead of s in the timer and interval settings!!!