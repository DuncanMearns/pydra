import time
from pydra_zmq.core import *
import numpy as np


ports = [
    ("tcp://*:5555", "tcp://localhost:5555"),
    ("tcp://*:5556", "tcp://localhost:5556"),
    ("tcp://*:5557", "tcp://localhost:5557")
]


zmq_config = {}


class DummyWorker(Worker):

    name = "dummy"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.t_last = 0

    def recv_frame(self, t, i, frame, **kwargs):
        t, i, frame = messaging.DATA.serializer("f").decode(t, i, frame)
        print(i, t - self.t_last, frame.shape)
        self.t_last = t

    def recv_indexed(self, t, i, data, **kwargs):
        t, i, data = messaging.DATA.serializer("i").decode(t, i, data)
        print(t - self.t_last, i, data)
        self.t_last = t

    def recv_timestamped(self, t, data, **kwargs):
        t, data = messaging.DATA.serializer("t").decode(t, data)
        print(t - self.t_last, data)
        self.t_last = t


MODULE_DUMMY = {
    "name": "dummy",
    "worker": DummyWorker,
    "subscriptions": (
        ("pydra", "", (messaging.DATA,)),
    ),
    "params": {}
}


config = {

    "modules": [MODULE_DUMMY]

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

    def new_frame(self):
        t = time.time()
        a = np.zeros((512, 512), dtype="uint8")
        self.send_frame(t, self.i, a)
        self.i += 1


def main():
    pydra = Pydra.run(config)
    pydra.hello_world()
    for f in range(10):
        time.sleep(0.01)
        pydra.new_frame()
    pydra.send_indexed(time.time(), -1000, {"hello": 0, "world": [1, 2, 3]})
    time.sleep(0.1)
    pydra.send_timestamped(time.time(), {"hello": "world"})
    time.sleep(0.5)
    pydra.exit()


if __name__ == "__main__":
    main()
