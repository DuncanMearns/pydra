from pydra import Pydra, ports, config
from pydra.core import Acquisition, Worker
from pydra.core.messaging import MESSAGE, FRAME
import time
import numpy as np


class TestAcquisition(Acquisition):

    name = "acquisition"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.i = 0

    def acquire(self):
        frame = np.zeros((200, 200))
        t = time.time()
        self.send_frame(t, self.i, frame)
        self.i += 1
        time.sleep(0.01)


class TestWorker(Worker):

    name = "worker"
    subscriptions = ("acquisition",)

    @MESSAGE
    def recv_frame(self, t, i, frame, **kwargs):
        t, i, frame = FRAME.decode(t, i, frame)
        return f"{self.name} received frame {i} at time {t} from {kwargs['source']}"


MODULE_ACQUISITION = {
    "worker": TestAcquisition,
    "params": {},
}


MODULE_WORKER = {
    "worker": TestWorker,
    "params": {},
}


config["modules"] = [MODULE_ACQUISITION, MODULE_WORKER]


if __name__ == "__main__":
    config = Pydra.configure(config, ports)
    pydra = Pydra(**config)
    time.sleep(1.0)
    ret, messages = pydra.request_messages()
    for (t, worker, message) in messages:
        print(message)
    pydra.exit()
