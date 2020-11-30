import time
from pydra_zmq.core import *
import numpy as np
from pathlib import Path
import os


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
        time.sleep(0.2)
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

    @messaging.logged
    def hello_world(self, **kwargs):
        print("hello world!", kwargs)
        return 1


MODULE_ACQUISITION = {
    "name": "acquisition",
    "worker": DummyAcquisition,
    "subscriptions": (
        # ("pydra", "", (messaging.DATA,)),
    ),
    "params": {},
    "save": True,
    "events": True
}


MODULE_TRACKER = {
    "name": "tracker",
    "worker": DummyTracker,
    "subscriptions": (
        ("pydra", "", (messaging.EVENT,)),
        ("acquisition", "", (messaging.DATA,)),
    ),
    "params": {},
    "save": True,
    "events": True
}


config = {

    "modules": [MODULE_ACQUISITION, MODULE_TRACKER],

}


class Pydra(bases.ZMQMain):

    name = "pydra"
    modules = []

    def __init__(self, working_dir, *args, **kwargs):
        # Initialize main
        super().__init__(*args, **kwargs)
        # Start workers
        for module in self.modules:
            module["worker"].start(zmq_config=zmq_config, **module["params"])
        # Start saving saver
        self.server = Saver.start(zmq_config=zmq_config)
        # Wait for processes to start
        time.sleep(0.5)
        # Set working directory
        self.working_dir = working_dir
        self.set_working_directory()

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
        # Configure saver
        saver_subs = []
        for module in cls.modules:
            sub = [module["name"]]
            if ("save" in module) and module["save"]:
                sub.append(1)
            else:
                sub.append(0)
            if ("events" in module) and module["events"]:
                sub.append(1)
            else:
                sub.append(0)
            saver_subs.append(sub)
        Saver.configure(zmq_config, (), saver_subs)
        # Get working directory
        working_dir = config.get("working_dir", os.getcwd())
        working_dir = Path(working_dir)
        return cls(working_dir, zmq_config=zmq_config)

    def set_working_directory(self):
        ret = self.send_event("set_working_directory", wait=True, source=self.name,
                              directory=str(self.working_dir))
        return ret

    def set_file_name(self):
        ret = self.send_event("set_working_directory", wait=True, source=self.name,
                              directory=str(self.working_dir))
        return ret


def main():
    pydra = Pydra.run(config)
    time.sleep(1.0)
    pydra.send_timestamped(time.time(), {"hello": "world"})
    time.sleep(0.5)
    pydra.exit()


if __name__ == "__main__":
    main()
