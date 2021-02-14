import time
from pydra_zmq.pydra import Pydra
from pydra_zmq.core import Saver, Worker, Acquisition, RemoteReceiver, messaging
from pydra_zmq.cameras import *
import numpy as np
from pathlib import Path
import os
import sys


ports = [
    ("tcp://*:5555", "tcp://localhost:5555"),
    ("tcp://*:5556", "tcp://localhost:5556"),
    ("tcp://*:5557", "tcp://localhost:5557"),
    ("tcp://*:5558", "tcp://localhost:5558"),
    ("tcp://*:5559", "tcp://localhost:5559")
]


class DummyAcquisition(Acquisition):

    name = "acquisition"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events["start_recording"] = self.start_recording
        self.n = 0

    def start_recording(self, **kwargs):
        self.n = 0

    def acquire(self):
        time.sleep(0.01)
        a = np.zeros((512, 512), dtype="uint8")
        t = time.time()
        self.send_frame(t, self.n, a)
        self.n += 1


class DummyTracker(Worker):

    name = "tracker"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.t_last = 0
        self.events["hello_world"] = self.hello_world

    @messaging.LOGGED
    def hello_world(self, **kwargs):
        print("hello world!")

    def recv_frame(self, t, i, frame, **kwargs):
        t, i, frame = messaging.DataMessage(messaging.FRAME).decode(t, i, frame)
        # print(kwargs["source"], i, t - self.t_last, frame.shape)
        # self.t_last = t
        self.send_indexed(t, i, dict(hello="world"))


MODULE_XIMEA = {
    "name": "ximea",
    "worker": XimeaCamera,
    "params": {},
    "subscriptions": (),
    "save": True,
    "group": ""
}


MODULE_ACQUISITION = {
    "name": "acquisition",
    "worker": DummyAcquisition,
    "params": {},
    "subscriptions": (),
    "save": True,
    "group": "",
    "codec": "xvid"
}


MODULE_TRACKER = {
    "name": "tracker",
    "worker": DummyTracker,
    "params": {},
    "subscriptions": (
        ("acquisition", "", (messaging.DataMessage,)),
    ),
    "save": True,
    "group": ""
}


_config = {

    # "zmq_config": {"remote_trigger": {"remote": "tcp://192.168.236.123:5996"}}
    "modules": [MODULE_ACQUISITION, MODULE_TRACKER],
    # "modules": [MODULE_XIMEA, MODULE_TRACKER],

}


def main():
    config = {
        "modules": [MODULE_ACQUISITION, MODULE_TRACKER],
    }
    pydra = Pydra.run(config)
    pydra.send_event("hello_world")
    time.sleep(5.0)
    pydra.start_recording()
    time.sleep(2.0)
    pydra.stop_recording()
    pydra.set_filename("new_name")
    pydra.start_recording()
    time.sleep(0.2)
    pydra.stop_recording()
    pydra.exit()


def ximea_test():
    import cv2
    config = {
        "modules": [MODULE_XIMEA, MODULE_TRACKER],
    }
    pydra = Pydra.run(config)
    pydra.send_event("set_params", frame_rate=300, exposure=1, frame_size=(100, 100))
    pydra.start_recording()
    for f in range(100):
        result = pydra._query("data")
        result = result[:-1]
        if len(result):
            name, frame, data = result
            frame = messaging.deserialize_array(frame)
            cv2.imshow("frame", frame)
            cv2.waitKey(10)
        else:
            time.sleep(0.1)
    pydra.stop_recording()
    pydra.exit()


if __name__ == "__main__":
    # ximea_test()
    main()
