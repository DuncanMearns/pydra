from pydra import Pydra
from pydra.core import Saver
import time


def no_config():
    Pydra.configure(savers=(Saver,))
    pydra = Pydra.run()
    time.sleep(3.)
    pydra.exit()


if __name__ == "__main__":
    no_config()
