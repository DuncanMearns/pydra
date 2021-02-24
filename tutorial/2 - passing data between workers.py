from pydra import Pydra, config, ports
from pydra.core.workers import Worker, Acquisition
import time


# Create a subclass of Acquisition
class SpamWorker(Acquisition):
    """Spam worker class"""

    # Every pydra worker must have a unique name
    name = "spam"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create a counter
        self.counter = 0

    def acquire(self, **kwargs):
        """Acquisition workers will call their acquire method once for every pass of the event loop."""
        # Get the current time
        now = time.time()
        # Broadcast a timestamped data message throughout the network
        self.send_timestamped(now, {"counter": self.counter})
        # Wait for one second
        time.sleep(1.0)
        # Increment the counter
        self.counter += 1


class EggsWorker(Worker):
    """Eggs worker class"""

    # Every pydra worker must have a unique name
    name = "eggs"

    # Add "foo" to subscriptions to allow Bar to receive data from the corresponding worker
    subscriptions = ("spam",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def recv_timestamped(self, t, data, **kwargs):
        """Method called whenever timestamped data messages are received."""
        print(f"Worker {self.name} received timestamped data from {kwargs['source']}.")
        print(f"At time: {t} the value of the counter was: {data['counter']}", end="\n\n")


# Create modules and add modules to Pydra's configuration
SPAM = {"worker": SpamWorker}
EGGS = {"worker": EggsWorker}

config["modules"] = [SPAM, EGGS]


if __name__ == "__main__":
    # Configure 0MQ connections
    Pydra.configure(config, ports)
    # Create the pydra object
    pydra = Pydra(**config)
    # Sleep for 10 seconds
    time.sleep(10.0)
    # Exit
    print("Exiting...")
    pydra.exit()
