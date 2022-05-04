from pydra import Pydra, config
from pydra.app import PydraApp
from pydra.core import Acquisition
from pydra.gui import ControlWidget
# from pydra_modules.cameras.widget import FramePlotter
from PyQt5 import QtWidgets
import numpy as np
import time


class AcquisitionWorker(Acquisition):
    """This is an acquisition worker. It will simulate a camera."""

    name = "acquisition"  # remember, every worker must have a unique name

    def __init__(self, value=0, *args, **kwargs):
        super().__init__(*args, **kwargs)  # always call super() constructor
        self.value = value  # this worker has a value attribute
        self.event_callbacks["set_value"] = self.set_value  # we can change the worker's value with a set_value event
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
        # time.sleep(0.01)


class AcquisitionWidget(ControlWidget):
    """This widget will be used to control our acquisition worker."""

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


# Create the acquisition module
ACQUISITION = {
    "worker": AcquisitionWorker,
    "params": {},  # params are passed to the constructor of the worker
    "controller": AcquisitionWidget,
    # "plotter": FramePlotter
}

config["modules"] = [ACQUISITION]


if __name__ == "__main__":
    PydraApp.run(config)
