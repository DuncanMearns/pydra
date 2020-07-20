from pydra import Experiment
import time


if __name__ == "__main__":
    pydra = Experiment()
    pydra.start()
    time.sleep(5.)
    pydra.stop()
