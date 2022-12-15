from pydra.app import PydraApp
from pydra import VideoSaver
from pydra.configuration import zmq_config
from pydra_modules.cameras.ximea_camera import XIMEA


VideoSaver.workers = ("ximea",)

XIMEA["params"]["camera_params"] = dict(frame_size=(300, 300), frame_rate=250., exposure=2000)

zmq_config["modules"] = [XIMEA]
zmq_config["savers"] = [VideoSaver]


if __name__ == "__main__":
    PydraApp.run(zmq_config)
