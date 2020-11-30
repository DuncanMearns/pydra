import time
from pydra_zmq.core import *
import numpy as np


ports = [
    ("tcp://*:5555", "tcp://localhost:5555"),
    ("tcp://*:5556", "tcp://localhost:5556"),
    ("tcp://*:5557", "tcp://localhost:5557"),
    ("tcp://*:5558", "tcp://localhost:5558"),
    ("tcp://*:5559", "tcp://localhost:5559")
]


zmq_config = {}


class DummyAcquisition(Acquisition):

    name = "acquisition"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

    def recv_frame(self, t, i, frame, **kwargs):
        t, i, frame = messaging.DATA.serializer("f").decode(t, i, frame)
        print(kwargs["source"], i, t - self.t_last, frame.shape)
        self.t_last = t

    def recv_indexed(self, t, i, data, **kwargs):
        t, i, data = messaging.DATA.serializer("i").decode(t, i, data)
        print(t - self.t_last, i, data)
        self.t_last = t

    def recv_timestamped(self, t, data, **kwargs):
        t, data = messaging.DATA.serializer("t").decode(t, data)
        print(t - self.t_last, data)
        self.t_last = t


MODULE_ACQUISITION = {
    "name": "acquisition",
    "worker": DummyAcquisition,
    "subscriptions": (
        # ("pydra", "", (messaging.DATA,)),
    ),
    "params": {}
}


MODULE_TRACKER = {
    "name": "tracker",
    "worker": DummyTracker,
    "subscriptions": (
        ("acquisition", "", (messaging.DATA,)),
    ),
    "params": {}
}


config = {

    "modules": [MODULE_ACQUISITION, MODULE_TRACKER]

}


class Pydra(zmq.ZMQMain):

    name = "pydra"
    modules = []

    def __init__(self, *args, **kwargs):
        # Start workers
        for module in self.modules:
            module["worker"].start(zmq_config=zmq_config, **module["params"])
        super().__init__(*args, **kwargs)
        time.sleep(0.5)
        self.i = 0

    @classmethod
    def run(cls, config):
        # Add modules
        try:
            cls.modules = config["modules"]
        except KeyError:
            cls.modules = []
        # Set the zmq configuration
        global zmq_config
        try:
            zmq_config.update(config["zmq_config"])
        except KeyError:
            global ports
            cls.configure(zmq_config, ports)
            for module in cls.modules:
                module["worker"].configure(zmq_config, ports, module["subscriptions"])
        return cls(zmq_config=zmq_config)

    def hello_world(self):
        self.send_message("hello world!")


def main():
    pydra = Pydra.run(config)
    pydra.hello_world()
    time.sleep(1.0)
    # pydra.send_timestamped(time.time(), {"hello": "world"})
    # time.sleep(0.5)
    pydra.exit()


if __name__ == "__main__":
    main()
