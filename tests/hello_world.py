from pydra import Pydra
from pydra.core import Worker
import time


class HelloWorld(Worker):

    name = "hello_world"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events["hello_world"] = self.hello_world

    def hello_world(self, **kwargs):
        print("HELLO WORLD!")


HELLOWORLD = {
    "worker": HelloWorld,
    "params": {}
}


modules = [HELLOWORLD]


def hello_world():
    Pydra.configure(modules=(HELLOWORLD,))
    pydra = Pydra()
    pydra.start_worker(HelloWorld)
    print("Sending hello_world event")
    time.sleep(0.1)
    pydra.send_event("hello_world")
    time.sleep(1.)
    pydra.exit()


if __name__ == "__main__":
    hello_world()
