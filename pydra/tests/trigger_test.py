from pydra import Pydra
from pydra.protocol.triggers import ZMQTrigger


def test_zmq_trigger(port):
    trigger = ZMQTrigger(port)
    pydra = Pydra.run(triggers={"zmq": trigger})
    pydra.triggers["zmq"].event_flag.wait()
    pydra.exit()


if __name__ == "__main__":
    test_zmq_trigger(r"tcp://localhost:5555")
