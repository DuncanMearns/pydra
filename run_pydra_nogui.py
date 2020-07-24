from pydra.pydra import Pydra
import time


if __name__ == "__main__":
    pydra = Pydra()
    pydra.start_pipeline()
    time.sleep(3.)
    pydra.start()
    time.sleep(3.)
    pydra.stop()
    pydra.stop_pipeline()
