import time
from pydra_zmq.core import Saver, Worker, Acquisition, messaging, bases
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

    @messaging.logged
    def hello_world(self, **kwargs):
        print("hello world!")

    def recv_frame(self, t, i, frame, **kwargs):
        t, i, frame = messaging.DATA(messaging.FRAME).decode(t, i, frame)
        # print(kwargs["source"], i, t - self.t_last, frame.shape)
        self.t_last = t
        self.send_indexed(t, i, dict(hello="world"))


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
        ("acquisition", "", (messaging.DATA,)),
    ),
    "save": True,
    "group": ""
}


config = {

    "modules": [MODULE_ACQUISITION, MODULE_TRACKER],

}


class Pydra(bases.ZMQMain):

    name = "pydra"
    modules = []

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
            if module["save"]:
                sub.append(1)
            else:
                sub.append(0)
            saver_subs.append(sub)
        Saver.configure(zmq_config, (), saver_subs)
        # Return configured pydra object
        return cls(zmq_config)

    def __init__(self, zmq_config, *args, **kwargs):
        # Initialize main
        super().__init__(zmq_config=zmq_config, *args, **kwargs)
        # Start workers
        for module in self.modules:
            module["worker"].start(zmq_config=zmq_config, **module["params"])
        # Start saving saver
        groups = {}
        for module in self.modules:
            group = module["group"]
            if group in groups:
                groups[group].append(module["name"])
            else:
                groups[group] = [module["name"]]
        self.saver = Saver.start(groups, None, zmq_config=zmq_config)
        # Wait for processes to start
        time.sleep(0.5)
        # Set working directory and filename
        working_dir = kwargs.get("working_dir", os.getcwd())
        self.working_dir = Path(working_dir)
        filename = kwargs.get("filename", "default_filename")
        self.filename = filename

    @messaging.event
    def start_recording(self):
        return "start_recording", dict(directory=str(self.working_dir), filename=str(self.filename))

    @messaging.event
    def stop_recording(self):
        return "stop_recording", {}

    @messaging.event
    def set_working_directory(self, directory):
        self.working_dir = directory
        return "set_working_directory", dict(directory=str(self.working_dir))

    @messaging.logged
    @messaging.event
    def set_filename(self, filename):
        self.filename = filename
        return "set_filename", dict(filename=str(self.filename))


def main():
    pydra = Pydra.run(config)
    # pydra.query("messages")
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


if __name__ == "__main__":
    main()
