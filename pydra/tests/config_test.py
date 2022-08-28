from pydra import Pydra, PydraApp, Configuration
import time


def test_pydra():
    pydra = Pydra.run()
    time.sleep(1.)
    pydra.exit()


def test_gui():
    PydraApp.run(Configuration())


if __name__ == "__main__":
    test_pydra()
    # test_gui()
