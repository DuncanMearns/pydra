import time
from pydra_zmq.pydra import Pydra
from pydra_zmq.core import RemoteReceiver, RemoteSender, messaging
from pydra_zmq.cameras import XimeaCamera
import cv2
import numpy as np


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


class ScanImageSender(RemoteSender):

    name = "scanimage"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events["start_recording"] = self.start_scanning
        self.events["stop_recording"] = self.stop_scanning
        self.events["release_scanimage"] = self.release_scanimage

    def start_scanning(self, **kwargs):
        ret = self.send_remote(1)
        ret = messaging.deserialize_int(ret)
        return ret

    def stop_scanning(self, **kwargs):
        ret = self.send_remote(2)
        ret = messaging.deserialize_int(ret)
        return ret

    def release_scanimage(self, **kwargs):
        ret = self.send_remote(0)
        ret = messaging.deserialize_int(ret)
        return ret


class TriggerReceiver(RemoteReceiver):

    name = "trigger_receiver"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @messaging.logged
    def trigger_received(self, val):
        return {"val": val, "event": True}

    def recv_remote(self, val, *args):
        val = messaging.deserialize_int(val)
        self.trigger_received(val)


class Hyperion(Pydra):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events["trigger_received"] = self.trigger_received
        self.number = 1

    def trigger_received(self, **kwargs):
        val = kwargs.get("val")
        if val:
            self.set_filename(self.filename[:-1] + str(self.number))
            print(f"Recording start {self.filename}...", end=" ")
            self.start_recording()
        else:
            self.stop_recording()
            print("finished.")
            self.number += 1


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
    "name": "trigger_receiver",
    "worker": TriggerReceiver,
    "params": {},
    "subscriptions": (),
    "save": True,
    "group": ""
}


config = {

    "modules": [MODULE_TAIL, MODULE_JAW, MODULE_SCANIMAGE],
    "zmq_config": {
        "trigger_receiver": {"receiver": ("tcp://*:5996", "tcp://localhost:5996")}
    }

}


def show_cameras():
    datamsg = messaging.ZMQMessage(str, np.ndarray, dict)
    pydra = Hyperion.run(config)
    pydra.send_event("set_params", target="tailcam", exposure=3, frame_size=(300, 300), gain=4)
    pydra.send_event("set_params", target="jawcam", exposure=0.5, frame_size=(300, 200))
    while True:
        data = pydra.query("data")
        if len(data):
            data = [datamsg.decode(*data[(3 * i):(3 * i) + 3]) for i in range(len(data) // 3)]
            for name, frame, _ in data:
                cv2.imshow(name, frame)
            k = cv2.waitKey(1)
            if k == 13:
                break
    pydra.exit()


def main():
    pydra = Hyperion.run(config)
    pydra.send_event("set_params", target="tailcam", exposure=3, frame_size=(300, 300), gain=4)
    pydra.send_event("set_params", target="jawcam", exposure=0.5, frame_size=(300, 200))
    pydra.set_working_directory(r"C:\DATA\Duncan\2020_12_09")
    pydra.set_filename(r"fish2_plane2_0001")
    cv2.namedWindow("exit")
    while True:
        pydra.receive_events()
        k = cv2.waitKey(1)
        if k == 13:
            break
    pydra.exit()
    return pydra


if __name__ == "__main__":
    # show_cameras()
    main()
