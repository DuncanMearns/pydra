from pydra import Pydra, ports, config
from pydra.core import Acquisition
from pydra.core.trigger import ZMQTrigger
import numpy as np
import time


class AcquisitionWorker(Acquisition):

    name = "acquisition"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.i = 0

    def acquire(self):
        frame = np.random.random((250, 250))
        frame *= 255
        frame = frame.astype("uint8")
        t = time.time()
        time.sleep(0.01)
        self.send_frame(t, self.i, frame)
        self.i += 1


ACQUISITION = {
    "worker": AcquisitionWorker,
    "params": {},
}


config["modules"] = [ACQUISITION]
config["trigger"] = ZMQTrigger("tcp://localhost:6002")


if __name__ == "__main__":
    config = Pydra.configure(config, ports)
    pydra = Pydra.start(working_dir="D:\pydra_tests", **config)
