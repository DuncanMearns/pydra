from pydra import PydraApp, config, CSVSaver, VideoSaver
from pydra_modules.cameras.ximea_camera import XIMEA

# Camera modules

CamWorker = XIMEA["worker"]


class TailCamera(CamWorker):
    name = "tail_camera"


class TailSaver(VideoSaver):
    name = "tail_camera_saver"
    workers = ("tail_camera",)


class JawCamera(CamWorker):
    name = "jaw_camera"


class JawSaver(VideoSaver):
    name = "jaw_camera_saver"
    workers = ("jaw_camera",)


TAIL_CAMERA = dict(XIMEA)
TAIL_CAMERA["worker"] = TailCamera
TAIL_CAMERA["params"] = dict(TAIL_CAMERA["params"])
TAIL_CAMERA["params"]["camera_params"] = dict(camera_id=0, frame_size=(300, 300), frame_rate=300)


JAW_CAMERA = dict(XIMEA)
JAW_CAMERA["worker"] = JawCamera
JAW_CAMERA["params"] = dict(JAW_CAMERA["params"])
JAW_CAMERA["params"]["camera_params"] = dict(camera_id=1, frame_size=(300, 300), frame_rate=300)


# Add modules to config

config["modules"] = [TAIL_CAMERA, JAW_CAMERA]


# Savers

CSVSaver.workers = ("speaker",)
config["savers"] = [TailSaver, JawSaver]


# Defaults

config["gui_params"].update({
        "directory": r"C:\DATA\Duncan",
        "filename": "test"
    })


if __name__ == "__main__":
    PydraApp.run(config)
