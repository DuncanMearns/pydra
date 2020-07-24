from pydra.pydra import Pydra
import time


if __name__ == "__main__":
    pydra = Pydra()
    pydra._start_processes()
    time.sleep(3.)
    pydra.start()
    time.sleep(3.)
    pydra.stop()
    pydra._join_processes()
