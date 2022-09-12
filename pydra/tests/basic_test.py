import time

from pydra.base import *


class Pydra(PydraMain):
    def __init__(self):
        super().__init__(publisher="tcp://*:5555")


class Worker(PydraWorker):
    def __init__(self):
        super().__init__(publisher="tcp://*:5556",
                         sender="tcp://localhost:5557",
                         subscriptions=[("PydraMain", "tcp://localhost:5555", (TRIGGER, EVENT))])

    def recv_trigger(self, source, t):
        super().recv_trigger(source, t)
        self.send_timestamped(t, dict(source=source))


class Saver(PydraSaver):

    subscriptions = ("Worker",)

    def __init__(self):
        super().__init__(publisher="tcp://*:5558", receiver="tcp://*:5557", subscriptions=())

    def recv_timestamped(self, t, data, **kwargs):
        print(self.name, time.time() - t, data)


class Backend(PydraBackend):
    def __init__(self):
        super().__init__(subscriptions=[("Worker", "tcp://localhost:5556", (DATA,))])

    def recv_timestamped(self, t, data, **kwargs):
        print(self.name, time.time() - t, data)


def main():
    p = Pydra()
    w = Worker()
    s = Saver()
    b = Backend()

    time.sleep(2.)

    p.send_trigger()
    w.receive_subscriptions(10)
    b.receive_subscriptions(10)
    s.receive_data(10)
    return


if __name__ == "__main__":
    main()
