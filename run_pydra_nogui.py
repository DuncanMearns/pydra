from pydra.pydra import Pydra
import time


if __name__ == "__main__":
    pydra = Pydra()
    pydra.run()
    time.sleep(5.)
    pydra.start_pipeline()
    time.sleep(5.)
    pydra.stop_pipeline()
    pydra.terminate()
