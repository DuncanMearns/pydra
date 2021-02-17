from pydra import Pydra, ports, config
from pydra.core.trigger import ZMQTrigger
from pydra.modules.cameras.widget import CameraWidget
from pydra.modules.cameras.workers import XimeaCamera


class TailCam(XimeaCamera):

    name = "tailcam"
    pipeline = "tail"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = 0


class JawCam(XimeaCamera):

    name = "jawcam"
    pipeline = "jaw"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = 1


TAILCAM = {
    "worker": TailCam,
    "params": {
        "frame_size": (300, 300),
        "frame_rate": 250.,
        "exposure": 3,
        "gain": 4
    },
    "widget": CameraWidget,
}


JAWCAM = {
    "worker": JawCam,
    "params": {
        "frame_size": (300, 300),
        "frame_rate": 100.,
        "exposure": 0.5,

        "min_exposure": 0.01
    },
    "widget": CameraWidget,
}


config["modules"] = [TAILCAM, JAWCAM]
config["trigger"] = ZMQTrigger("tcp://192.168.236.101:5555")


if __name__ == "__main__":
    config = Pydra.configure(config, ports)
    pydra = Pydra.run(working_dir=r"C:\DATA\Duncan\2021_02_17", **config)
