from pydra import Pydra
from pydra.protocol import Protocol
import time


def main():
    from pydra.tests.hello_world import modules
    pydra = Pydra.run(modules=modules)
    # Build protocol
    protocol = Protocol()
    protocol.addPause(1)
    protocol.addEvent(pydra, "hello_world")
    protocol.addPause(1)
    protocol.addEvent(pydra, "hello_world")
    protocol.addPause(1)
    # Run protocol
    print("starting protocol")
    protocol.run()
    time.sleep(2)
    print("restarting")
    protocol.restart()
    protocol.wait()
    print("finished")
    pydra.exit()


if __name__ == "__main__":
    main()
