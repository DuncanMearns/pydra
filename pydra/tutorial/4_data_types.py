from pydra import Pydra, config, ports
from pydra.core.workers import Worker
import time
import numpy as np


class DataSender(Worker):

    name = "sender"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create event for receiving messages from Pydra
        self.events["send_data"] = self.send_data
        # Create index attribute
        self.index = 0

    def send_data(self, data_type, **kwargs):
        # Get the current time
        now = time.time()
        data = dict(hello="world", spam="eggs")
        if data_type == "timestamped":
            # Send a timestamped data message
            self.send_timestamped(now, data)
        elif data_type == "indexed":
            # Send indexed data message
            self.send_indexed(now, self.index, data)
            self.index += 1
        elif data_type == "frame":
            # Send indexed frame message
            frame = np.random.rand(300, 200)
            self.send_frame(now, self.index, frame)
            self.index += 1
        else:
            print(f"Data type: {data_type} not understood.")


class DataReceiver(Worker):

    name = "receiver"
    subscriptions = ("sender",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def recv_timestamped(self, t, data, **kwargs):
        """Method called whenever timestamped data messages are received."""
        print(f"Worker {self.name} received timestamped data from {kwargs['source']}.")
        print(f"The timestamp is: {t}")
        print(f"The data is: {data}\n")

    def recv_indexed(self, t, i, data, **kwargs):
        """Method called whenever indexed data messages are received."""
        print(f"Worker {self.name} received indexed data from {kwargs['source']}.")
        print(f"The timestamp is: {t}")
        print(f"The index is: {i}")
        print(f"The data is: {data}\n")

    def recv_frame(self, t, i, frame, **kwargs):
        """Method called whenever frame data messages are received."""
        print(f"Worker {self.name} received frame data from {kwargs['source']}.")
        print(f"The timestamp is: {t}")
        print(f"The index is: {i}")
        print(f"The frame has shape: {frame.shape}\n")


# Create modules and add modules to Pydra's configuration
SENDER = {"worker": DataSender}
RECEIVER = {"worker": DataReceiver}

config["modules"] = [SENDER, RECEIVER]


if __name__ == "__main__":
    # Configure and create pydra object
    Pydra.configure(config, ports)
    pydra = Pydra(**config)
    # Send events for different message types
    pydra.send_event("send_data", data_type="timestamped")
    time.sleep(1.0)
    pydra.send_event("send_data", data_type="indexed")
    time.sleep(1.0)
    pydra.send_event("send_data", data_type="frame")
    time.sleep(1.0)
    pydra.send_event("send_data", data_type="indexed")
    time.sleep(1.0)
    # Exit
    print("Exiting.")
    pydra.exit()
