from pydra import Pydra, config, ports
from pydra.modules.optogenetics import OPTOGENETICS
from pydra.modules.cameras.widget import CameraWidget, FramePlotter
from pydra.modules.cameras.ximea import XimeaCamera


class TailCam(XimeaCamera):

    name = "tailcam"
    pipeline = "tail"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.id = 1


class JawCam(XimeaCamera):

    name = "jawcam"
    pipeline = "jaw"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.id = 0


TAILCAM = {

    "worker": TailCam,

    "params": {

        "camera_id": 1,

        "frame_size": (368, 312),
        "frame_rate": 300.,
        "exposure": 0.5,
        "gain": 1.,

        "min_size": (250, 250),
        "max_size": (1280, 1024),
        "min_gain": 0.,
        "max_gain": 20.,
        "min_exposure": 0.001,
        "max_exposure": 10.,
    },

    "controller": CameraWidget,
    "plotter": FramePlotter
}


JAWCAM = {

    "worker": JawCam,

    "params": {

        "camera_id": 0,

        "frame_size": (368, 312),
        "frame_rate": 300.,
        "exposure": 0.5,
        "gain": 1.,

        "min_size": (250, 250),
        "max_size": (1280, 1024),
        "min_gain": 0.,
        "max_gain": 20.,
        "min_exposure": 0.001,
        "max_exposure": 10.,
    },

    "controller": CameraWidget,
    "plotter": FramePlotter

}


config["modules"] = [TAILCAM, JAWCAM, OPTOGENETICS]
# config["modules"] = [OPTOGENETICS]


if __name__ == "__main__":
    Pydra.configure(config, ports)
    Pydra.run(working_dir=r"D:\\DATA", **config)
