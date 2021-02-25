from pydra import Pydra, ports, config
from pydra.core import Worker
import time


class TestWorker(Worker):

    name = "test"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events["dummy"] = self.dummy

    def dummy(self, **kwargs):
        return


MODULE_TEST = {
    "worker": TestWorker,
    "params": {},
}


config["modules"] = [MODULE_TEST]


if __name__ == "__main__":
    config = Pydra.configure(config, ports)
    pydra = Pydra(**config)
    time.sleep(1.0)
    pydra.exit()
