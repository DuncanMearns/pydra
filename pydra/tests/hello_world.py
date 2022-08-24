from pydra import Pydra, Worker
import time


class HelloWorld(Worker):

    name = "hello_world"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_callbacks["hello_world"] = self.hello_world

    def hello_world(self, **kwargs):
        print("HELLO WORLD!")


HELLOWORLD = {
    "worker": HelloWorld,
    "params": {}
}


modules = [HELLOWORLD]


def hello_world():
    pydra = Pydra.run(modules=modules)
    print("Sending hello_world event")
    pydra.send_event("hello_world")
    time.sleep(1.)
    pydra.exit()


def no_config():
    pydra = Pydra.run()
    time.sleep(1.)
    pydra.exit()


if __name__ == "__main__":
    hello_world()
    # no_config()
