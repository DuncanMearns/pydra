from pydra import Pydra, ports, config
from pydra.core import Worker, Acquisition
from pydra.gui.module import ModuleWidget, DisplayProxy
from PyQt5 import QtWidgets
import pyqtgraph as pg
import numpy as np
import time
from collections import deque


class AcquisitionWorker(Acquisition):

    name = "acquisition"

    def __init__(self, value, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = value
        self.i = 0
        self.events["set_value"] = self.set_value

    def set_value(self, value=0, **kwargs):
        self.value = value
        print(f"{self.name}.value was set to: {self.value}")

    def acquire(self):
        frame = np.random.random((250, 250))
        frame *= 255
        frame = frame.astype("uint8")
        t = time.time()
        time.sleep(0.01)
        self.send_frame(t, self.i, frame)
        self.i += 1


class FrameDisplay(pg.GraphicsLayoutWidget):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.image_plot = self.addPlot(row=0, col=0)
        self.image_plot.setMouseEnabled(False, False)
        self.image_plot.setAspectLocked()
        self.image_plot.hideAxis('bottom')
        self.image_plot.hideAxis('left')
        self.image = pg.ImageItem()
        self.image_plot.addItem(self.image)

    def show(self, image):
        if image.shape:
            self.image.setImage(image)


class AcquisitionWidget(ModuleWidget):

    display = FrameDisplay

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWidget(QtWidgets.QWidget())
        self.widget().setLayout(QtWidgets.QFormLayout())
        self.value_widget = QtWidgets.QSpinBox()
        self.value_widget.valueChanged.connect(self.set_value)
        self.widget().layout().addRow("Value:", self.value_widget)

    def set_value(self, val):
        self.send_event("set_value", value=val)

    def enterRunning(self):
        self.setEnabled(False)

    def enterIdle(self):
        self.setEnabled(True)

    def updateData(self, data, frame=None, **displays):
        self._display.show(frame)


class TrackingWorker(Worker):

    name = "tracking"
    subscriptions = ("acquisition",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def recv_frame(self, t, i, frame, **kwargs):
        data = dict(x=np.random.rand(), y=np.random.rand())
        self.send_indexed(t, i, data)


class TrackingPlotter(pg.GraphicsLayoutWidget):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.initUI()
        self.t0 = time.time()

    def initUI(self):
        # Create param plots
        self._plotters = {}
        self.plot_data = {}
        self.caches = {}
        for i, param in enumerate(("x", "y")):
            param_plot = self.addPlot(row=i + 1, col=0, title=param)
            if len(self._plotters):
                param_plot.setXLink(self._plotters[list(self._plotters.keys())[0]])
            plot_data = param_plot.plot([], [])
            self._plotters[param] = param_plot
            self.caches[param] = deque(maxlen=10000)
            self.plot_data[param] = plot_data

    def update(self, **params):
        t = np.array(params.get("time", [])) - self.t0
        for data_name, data in params.get("data", {}).items():
            try:
                self.caches[data_name].extend(zip(t, data))
                show_data = np.array(self.caches[data_name])
                self.plot_data[data_name].setData(show_data[:, 0], show_data[:, 1])
            except KeyError:
                pass


class TrackingDisplay(DisplayProxy):

    display = TrackingPlotter

    def updateData(self, data, frame=None, **displays):
        self._display.update(**data)


ACQUISITION = {
    "worker": AcquisitionWorker,
    "params": {"value": 1},
    "widget": AcquisitionWidget,
}


TRACKING = {
    "worker": TrackingWorker,
    "widget": TrackingDisplay
}


config["modules"] = [ACQUISITION, TRACKING]


if __name__ == "__main__":
    config = Pydra.configure(config, ports)
    pydra = Pydra.run(working_dir="D:\pydra_tests", **config)
