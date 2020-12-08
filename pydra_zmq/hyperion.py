import time
from pydra_zmq.pydra import Pydra
from pydra_zmq.core import RemoteReceiver, RemoteSender, messaging
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
        return {"val": val}

    def recv_remote(self, val, *args):
        self.trigger_received(val)


class Hyperion(Pydra):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events["trigger_received"] = self.trigger_received

    def trigger_received(self, **kwargs):
        val = kwargs.get("val")
        if val:
            self.start_recording()
        else:
            self.stop_recording()


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
        "scanimage": {"receiver": "tcp://192.168.236.123:5996"}
    }

}


def main():
    pydra = Pydra.run(config)
    pydra.send_event("set_params", target="tailcam", exposure=3, frame_size=(300, 300), gain=4)
    pydra.send_event("set_params", target="jawcam", exposure=1, frame_size=(300, 200))
    pydra.set_working_directory(r"C:\DATA\Duncan\2020_12_04")
    pydra.set_filename(r"test_video")
    return pydra


if __name__ == "__main__":
    main()
