from pydra import Pydra
import time


def test_pydra():
    pydra = Pydra.run()
    time.sleep(1.)
    pydra.exit()


if __name__ == "__main__":
    test_pydra()
