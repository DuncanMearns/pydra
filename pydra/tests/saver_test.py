from pydra import Pydra
import time
import os


def test_frame_saver():
    from pydra.tests.configs.frame_acquisition import config
    pydra = Pydra.run(config=config)
    time.sleep(1.)
    pydra.send_event("set_value", value=10)
    time.sleep(1.)
    pydra.send_event("start_recording", directory=os.getcwd(), filename="saver_test")
    time.sleep(5.)
    pydra.send_event("stop_recording")
    time.sleep(1.)
    pydra.exit()


if __name__ == "__main__":
    test_frame_saver()
