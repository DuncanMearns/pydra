import time
from pydra_zmq.core import *


ports = [
    ("tcp://*:5555", "tcp://localhost:5555"),
    ("tcp://*:5556", "tcp://localhost:5556"),
    ("tcp://*:5557", "tcp://localhost:5557")
]


zmq_config = {}


DummyWorker = type("DummyWorker", (Worker,), dict(name="dummy"))


MODULE_DUMMY = {
    "name": "dummy",
    "worker": DummyWorker,
    "subscriptions": (),
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
        self.exit()


def main():
    pydra = Pydra.run(config)
    pydra.hello_world()


if __name__ == "__main__":
    main()
