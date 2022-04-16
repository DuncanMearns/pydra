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
    Pydra.configure(modules=modules)
    pydra = Pydra._run()
    print("Sending hello_world event")
    pydra.send_event("hello_world")
    time.sleep(1.)
    pydra.exit()


def no_config():
    Pydra.configure()
    pydra = Pydra._run()
    pydra.exit()


if __name__ == "__main__":
    hello_world()
    # no_config()
