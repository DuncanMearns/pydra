from pydra import Pydra, ports, config
from pydra.core import Worker, Acquisition
from pydra.gui import ControlWidget
from modules.cameras.widget import FramePlotter
from PyQt5 import QtWidgets
import numpy as np
import time


class AcquisitionWorker(Acquisition):
    """This is an camera worker. It will simulate a camera."""

    name = "camera"  # remember, every worker must have a unique name

    def __init__(self, value, *args, **kwargs):
        super().__init__(*args, **kwargs)  # always call super() constructor
        self.value = value  # this worker has a value attribute
        self.events["set_value"] = self.set_value  # we can change the worker's value with a set_value event
        self.i = 0  # this will store the frame index

    def set_value(self, value=0, **kwargs):
        """Method called by a set_value event from pydra"""
        self.value = value
        print(f"{self.name}.value was set to: {self.value}")

    def acquire(self):
        """Method called each pass of the event loop. Generate a frame of random numbers."""
        # Create a uint8 frame of frandom numbers
        frame = np.random.random((250, 250))
        frame *= 255
        frame = frame.astype("uint8")
        # Get the time stamp
        t = time.time()
        # Broadcast frame data through the network
        self.send_frame(t, self.i, frame)
        # Increment the frame index
        self.i += 1
        # Sleep (simulates the camera frame rate)
        time.sleep(0.01)


class AcquisitionWidget(ControlWidget):
    """This widget will be used to control our camera worker."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # call to super()
        self.setLayout(QtWidgets.QFormLayout())
        # Add a spinbox for changing the value attribute of our worker
        self.value_widget = QtWidgets.QSpinBox()
        # Connect the value spinbox to the set_value method
        self.value_widget.valueChanged.connect(self.set_value)
        # Add our spinbox to the widget
        self.layout().addRow("Value:", self.value_widget)

    def set_value(self, val):
        """Method called whenever the value changed in the widget."""
        self.send_event("set_value", value=val)  # send a "set_value" event with a "value" keyword

    def enterRunning(self):
        """This is called whenever the record button is clicked in the GUI and the GUI enters the 'running' state."""
        self.setEnabled(False)  # disable the widget whenever pydra is recording

    def enterIdle(self):
        """This is called whenever a recording finishes and the GUI enters the 'idle' state."""
        self.setEnabled(True)  # enable the widget again once recording finishes


class TrackingOverlay(FramePlotter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def updatePlots(self, data_cache, **kwargs):
        super().dynamicUpdate(data_cache, **kwargs)
        x = kwargs["tracking"]["x"]
        y = kwargs["tracking"]["y"]
        points = 125 + np.array([x, y]) * 50  # create numpy array
        self.updateOverlay("frame", *points)


class TrackingWorker(Worker):
    """This worker will simulate a tracking worker."""

    name = "tracking"  # the worker is called "tracking"
    subscriptions = ("camera",)  # it receives messages from "camera"

    def recv_frame(self, t, i, frame, **kwargs):
        """This method is called whenever the worker receives frame data."""
        data = dict(x=np.random.rand(), y=np.random.rand())  # create some random x, y coordinates
        # Send coordinates as indexed data
        self.send_indexed(t, i, data)  # the timestamp and index should be the same as the received frame!!!


# Create the camera module
ACQUISITION = {
    "worker": AcquisitionWorker,
    "params": {"value": 0},  # params are passed to the constructor of the worker
    "controller": AcquisitionWidget,
    "plotter": TrackingOverlay
}

# Create the tracking module
TRACKING = {
    "worker": TrackingWorker
}

# Add modules to config
config["modules"] = [ACQUISITION, TRACKING]


if __name__ == "__main__":
    # Run pydra
    config = Pydra.configure(config, ports)
    pydra = Pydra.run(working_dir="D:\pydra_tests", **config)
