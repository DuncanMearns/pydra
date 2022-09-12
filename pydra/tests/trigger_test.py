from pydra import Pydra, PydraApp
from pydra.protocol.triggers import ZMQTrigger


def test_zmq_trigger():
    from pydra.configuration import port_manager
    pub, sub = port_manager.next()
    print("PUB:", pub, "SUB:", sub)
    trigger = ZMQTrigger(sub)
    pydra = Pydra.run(triggers={"zmq": trigger})
    pydra.triggers["zmq"].event_flag.wait()
    pydra.exit()


def test_gui():
    from pydra.tests.configs.frame_acquisition import config
    from pydra.protocol import ZMQTrigger
    from pydra.configuration import port_manager
    pub, sub = port_manager.next()
    print("PUB:", pub, "SUB:", sub)
    config["triggers"] = {"zmq": ZMQTrigger(sub)}
    PydraApp.run(config)


if __name__ == "__main__":
    # test_zmq_trigger()
    test_gui()
