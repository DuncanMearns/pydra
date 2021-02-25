from pydra import Pydra, ports, config
from pydra.core import Worker, Acquisition
from pydra.gui.module import ModuleWidget, DisplayProxy
from PyQt5 import QtWidgets
import numpy as np
import time


class AcquisitionWorker(Acquisition):
    """This is an acquisition worker. It will simulate a camera."""

    name = "acquisition"  # remember, every worker must have a unique name

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


class AcquisitionWidget(ModuleWidget):
    """This widget will be used to control our acquisition worker."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # call to super()
        # Create a widget with a form layout
        self.setWidget(QtWidgets.QWidget())
        self.widget().setLayout(QtWidgets.QFormLayout())
        # Add a spinbox for changing the value attribute of our worker
        self.value_widget = QtWidgets.QSpinBox()
        # Connect the value spinbox to the set_value method
        self.value_widget.valueChanged.connect(self.set_value)
        # Add our spinbox to the widget
        self.widget().layout().addRow("Value:", self.value_widget)

    def set_value(self, val):
        """Method called whenever the value changed in the widget."""
        self.send_event("set_value", value=val)  # send a "set_value" event with a "value" keyword

    def enterRunning(self):
        """This is called whenever the record button is clicked in the GUI and the GUI enters the 'running' state."""
        self.setEnabled(False)  # disable the widget whenever pydra is recording

    def enterIdle(self):
        """This is called whenever a recording finishes and the GUI enters the 'idle' state."""
        self.setEnabled(True)  # enable the widget again once recording finishes

    def create_plotter(self, *args, **kwargs):
        """This method allows us to create a plotter widget for showing data broadcast through Pydra's network by the
        associated worker. By default, ModuleWidget's have an associated plotter (accessed via the plotter attribute).
        """
        super().create_plotter(*args, **kwargs)  # call to super creates an instance of a pydra.gui.plotter.Plotter
        self.plotter.addImagePlot("video", pen=None, symbol='o')  # add an image plot to the plotter called "video"

    def updatePlots(self, data, frame=None, **plotters):
        """This method is called whenever data are received from the associated worker. By default, the pydra GUI update
        rate is ~30 Hz. The data argument is a dictionary that contains timestamp and indexed data. The frame argument
        contains the last frame sent by the worker - if the worker has sent any frames at all."""
        self.plotter.updateImage("video", frame)  # update the image plot called "video" with the frame


class TrackingWorker(Worker):
    """This worker will simulate a tracking worker."""

    name = "tracking"  # the worker is called "tracking"
    subscriptions = ("acquisition",)  # it receives messages from "acquisition"

    def recv_frame(self, t, i, frame, **kwargs):
        """This method is called whenever the worker receives frame data."""
        data = dict(x=np.random.rand(), y=np.random.rand())  # create some random x, y coordinates
        # Send coordinates as indexed data
        self.send_indexed(t, i, data)  # the timestamp and index should be the same as the received frame!!!


class TrackingDisplay(DisplayProxy):
    """We do not need a ModuleWidget to control our TrackingWorker from the GUI, since it just blindly tracks all frames
    received from the AcquisitionWorker. However, we do want to plot the x, y coordinates we receive. For this reason,
    we must create a DisplayProxy widget instead."""

    def create_plotter(self, *args, **kwargs):
        """DisplayProxy is a subclass of ModuleWidget and has the same methods. Here, we can create plots."""
        super().create_plotter(*args, **kwargs)
        self.plotter.addParamPlot("x")  # add a time series plot for the x-coordinate
        self.plotter.addParamPlot("y")  # add a time series plot for the y-coordinate

    def updatePlots(self, data, frame=None, **plotters):
        """This method will receive all newly tracked data from the TrackingWorker via the data argument."""
        self.plotter.update(data)  # new data can be passed to the plotter's update method
        # Sometimes you might want to overlay or plot data from one worker on the plotter of another. For this purpose,
        # all other plotters in the GUI are passed to updatePlots as keyword arguments
        video_plotter = plotters["acquisition"]  # this accesses the plotter associated with the acquisition worker
        xy_data = data["data"]  # get all newly acquired data values
        x_data, y_data = xy_data["x"], xy_data["y"]  # get all new x values and y values
        points = 125 + np.array([x_data, y_data]).T * 50  # create numpy array
        video_plotter.updateOverlay("video", points)  # update the overlay of the plotter called "video"

    def enterRunning(self):
        """Clear the plotter whenever we start recording."""
        self.plotter.clear_data()


# Create the acquisition module
ACQUISITION = {
    "worker": AcquisitionWorker,
    "params": {"value": 0},  # params are passed to the constructor of the worker
    "widget": AcquisitionWidget,
}

# Create the tracking module
TRACKING = {
    "worker": TrackingWorker,
    "widget": TrackingDisplay
}

# Add modules to config
config["modules"] = [ACQUISITION, TRACKING]


if __name__ == "__main__":
    # Run pydra
    config = Pydra.configure(config, ports)
    pydra = Pydra.run(working_dir="D:\pydra_tests", **config)
