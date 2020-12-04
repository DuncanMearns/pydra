import time
from pydra_zmq.pydra import Pydra
from pydra_zmq.core import RemoteWorker, messaging
from pydra_zmq.cameras import XimeaCamera
import cv2


ports = [
    ("tcp://*:5555", "tcp://localhost:5555"),
    ("tcp://*:5556", "tcp://localhost:5556"),
    ("tcp://*:5557", "tcp://localhost:5557"),
    ("tcp://*:5558", "tcp://localhost:5558"),
    ("tcp://*:5559", "tcp://localhost:5559")
]


class TailCam(XimeaCamera):

    name = "tailcam"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = 0


class JawCam(XimeaCamera):

    name = "jawcam"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = 1


class ScanImage(RemoteWorker):

    name = "scanimage"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


MODULE_TAIL = {
    "name": "tailcam",
    "worker": TailCam,
    "params": {},
    "subscriptions": (),
    "save": True,
    "group": ""
}


MODULE_JAW = {
    "name": "jawcam",
    "worker": JawCam,
    "params": {},
    "subscriptions": (),
    "save": True,
    "group": "_jaw"
}


MODULE_SCANIMAGE = {
    "name": "scanimage",
    "worker": ScanImage,
    "params": {},
    "subscriptions": (),
    "save": True,
    "group": ""
}


config = {

    "modules": [MODULE_TAIL, MODULE_JAW, MODULE_SCANIMAGE],
    "zmq_config": {
        "scanimage": {"remote": "tcp://192.168.236.123:5996"}
    }

}


def main():
    pydra = Pydra.run(config)
    pydra.send_event("set_params", target="tailcam", exposure=3, frame_size=(300, 300), gain=4)
    pydra.send_event("set_params", target="jawcam", exposure=1, frame_size=(300, 200))
    pydra.set_working_directory(r"C:\DATA\Duncan\2020_12_04")
    pydra.set_filename(r"test_video")
    time.sleep(3.)
    # for f in range(1000):
    #     result = pydra.query("data")
    #     result = result[:-1]
    #     if len(result):
    #         for i in range(len(result) // 3):
    #             name, frame, data = result[(3 * i) : (3 * i) + 3]
    #             name = messaging.deserialize_string(name)
    #             frame = messaging.deserialize_array(frame)
    #             cv2.imshow(name, frame)
    #             cv2.waitKey(1)
    pydra.start_recording()
    time.sleep(3.0)
    pydra.stop_recording()
    # log = pydra.request_log()
    # print(log)
    pydra.exit()


if __name__ == "__main__":
    main()
