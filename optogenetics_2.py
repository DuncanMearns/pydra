from pydra import Pydra #, config, ports
from pydra.modules.optogenetics import OPTOGENETICS
from pydra.modules.cameras.ximea import XIMEA
# from pydra.modules.tracking.tail_tracker import TAIL_TRACKER, TailOverlay


# XIMEA["params"] = {
#
#     "frame_size": (368, 312),
#     "frame_rate": 200.,
#     "exposure": 2000,
#     "gain": 1.,
#
#     "min_size": (250, 250),
#     "max_size": (1280, 1024),
#     "min_gain": 0.,
#     "max_gain": 20.,
#     "min_exposure": 0.001,
#     "max_exposure": 10.}
#
# }
# XIMEA["plotter"] = TailOverlay
#
#
# TAIL_TRACKER["worker"].subscriptions = ("ximea",)
# TAIL_TRACKER["params"]["acquisition_worker"] = "ximea"


# config["modules"] = [XIMEA, OPTOGENETICS]#, TAIL_TRACKER]

ports = [
    ("tcp://*:5560", "tcp://localhost:5560"),
    ("tcp://*:5561", "tcp://localhost:5561"),
    ("tcp://*:5562", "tcp://localhost:5562"),
    ("tcp://*:5563", "tcp://localhost:5563"),
    ("tcp://*:5564", "tcp://localhost:5564")
]


config = {

    "connections": {

        "pydra": {
            "publisher": "tcp://*:6002",
            "receiver": "tcp://localhost:6003",
            "port": "tcp://localhost:6002"
        },

        "saver": {
            "sender": "tcp://*:6003",
            "subscriptions": []
        },

    },

    "modules": [],

    "trigger": None

}

config["modules"] = [OPTOGENETICS]


if __name__ == "__main__":
    Pydra.configure(config, ports)
    Pydra.run(working_dir=r"D:\\DATA\\Martin_opto\\", **config)

### Changes made: we set Pydra to process ms instead of s in the timer and interval settings!!!