from pydra import Pydra
from pydra.tests.frame_acquisition import config
import time


def test_frame_saver():
    pydra = Pydra.run(config=config)
    time.sleep(1.)
    pydra.send_event("set_value", value=10)
    time.sleep(1.)
    pydra.filename = "test_video"
    pydra.start_recording()
    time.sleep(5.)
    pydra.stop_recording()
    time.sleep(1.)
    pydra.exit()


if __name__ == "__main__":
    test_frame_saver()
