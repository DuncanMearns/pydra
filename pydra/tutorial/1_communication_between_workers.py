from pydra import Pydra, config, ports
from pydra.core.workers import Worker
import time


class SpamWorker(Worker):
    """Spam worker class"""

    # Every pydra worker must have a unique name
    name = "spam"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add an event called "spam" to the worker and map it to a corresponding method
        self.events["spam"] = self.spam_event

    def spam_event(self, **kwargs):
        """Method called when event called "spam" is received."""
        print(f"Worker {self.name} received event called 'spam' from {kwargs['source']}")
        self.send_event("eggs")


class EggsWorker(Worker):
    """Eggs worker class"""

    # Every pydra worker must have a unique name
    name = "eggs"

    # Add "foo" to subscriptions to allow Bar to receive events from the corresponding worker
    subscriptions = ("spam",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add an event called "eggs" to the worker and map it to a corresponding method
        self.events["eggs"] = self.eggs_event

    def eggs_event(self, **kwargs):
        """Method called when event called "eggs" is received."""
        print(f"Worker {self.name} received event called 'eggs' from {kwargs['source']}")


# Create modules and add modules to Pydra's configuration
SPAM = {"worker": SpamWorker}
EGGS = {"worker": EggsWorker}

config["modules"] = [SPAM, EGGS]


if __name__ == "__main__":
    # Configure 0MQ connections
    Pydra.configure(config, ports)
    # Create the pydra object
    pydra = Pydra(**config)
    # Send an event called "spam" to the network
    pydra.send_event("spam")
    # Sleep for one second
    time.sleep(1.0)
    # Exit
    pydra.exit()
