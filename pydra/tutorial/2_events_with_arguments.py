from pydra import Pydra, config, ports
from pydra.core.main.workers import Worker
import time


class SpamWorker(Worker):
    """Spam worker class"""

    # Every pydra worker must have a unique name
    name = "spam"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add an event called "spam" to the worker and map it to a corresponding method
        self.events["spam"] = self.spam_event
        # Create a value attribute
        self.value = 0

    def spam_event(self, value, **kwargs):
        """Method called when event called "spam" is received. Takes an argument, value."""
        print(f"Worker {self.name} received event called 'spam' from {kwargs['source']} with value {value}")
        # Set the value attribute
        self.value = value


# Create modules and add modules to Pydra's configuration
config["modules"] = [{"worker": SpamWorker}]


if __name__ == "__main__":
    # Configure 0MQ connections
    Pydra.configure(config, ports)
    # Create the pydra object
    pydra = Pydra(**config)
    # Change the value of spam every second
    for i in range(10):
        pydra.send_event("spam", value=i)
        time.sleep(1.0)
    # Exit
    pydra.exit()
