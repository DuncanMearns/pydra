from pydra import Pydra, PydraModule, Worker
import time


class HelloWorld(Worker):

    name = "hello_world"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_callbacks["hello_world"] = self.hello_world

    def hello_world(self, **kwargs):
        print("HELLO WORLD!")


modules = [PydraModule(HelloWorld)]


def hello_world():
    pydra = Pydra.run(modules=modules)
    print("Sending hello_world event")
    pydra.send_event("hello_world")
    time.sleep(1.)
    pydra.exit()


if __name__ == "__main__":
    hello_world()
