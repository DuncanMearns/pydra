from PyQt5 import QtWidgets
import pyqtgraph as pg
import numpy as np
from pyqtgraph.dockarea import DockArea, Dock
from .states import Stateful
pg.setConfigOption("imageAxisOrder", "row-major")


class DisplayContainer(Stateful, QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLayout(QtWidgets.QVBoxLayout())
        self._dock_area = DockArea()
        self.layout().addWidget(self._dock_area)

    def add(self, name: str, widget) -> None:
        dock = Dock(name)
        dock.addWidget(widget)
        self._dock_area.addDock(dock)


class Plotter(Stateful, pg.GraphicsLayoutWidget):

    def __init__(self, name, *args, **kwargs):
        super().__init__()
        self.name = name
        self.image_plots = {}
        self.images = {}
        self.overlay_data = {}
        self.param_plots = {}
        self.param_data = {}

    def addImagePlot(self, name, **kwargs):
        # Create plot item
        plot = pg.PlotItem()
        plot.setMouseEnabled(False, False)
        plot.setAspectLocked()
        plot.hideAxis('bottom')
        plot.hideAxis('left')
        plot.getViewBox().invertY(True)
        # Create image and data items
        image = pg.ImageItem()
        data = pg.PlotDataItem([], [], **kwargs)
        # Add image and data to plot
        plot.addItem(image)
        plot.addItem(data)
        # Update self
        self.image_plots[name] = plot
        self.images[name] = image
        self.overlay_data[name] = data
        self.addItem(plot)
        self.nextRow()

    def addParamPlot(self, name, linked=True, **kwargs):
        # Create plot item
        plot = pg.PlotItem(title=name)
        if linked and len(self.param_plots):
            plot.setXLink(self.param_plots[list(self.param_plots.keys())[0]])
        # Create plot data
        data = plot.plot([], [], **kwargs)
        # Update self
        self.param_plots[name] = plot
        self.param_data[name] = data
        self.addItem(plot)
        self.nextRow()

    def updateImage(self, name: str, image: np.ndarray):
        if image.shape and name in self.images:
            self.images[name].setImage(image)

    def updateOverlay(self, name: str, x, y):
        if name in self.overlay_data:
            self.overlay_data[name].setData(x, y)

    def updateParam(self, name: str, x, y):
        if name in self.param_data:
            self.param_data[name].setData(x, y)

    def clear_data(self):
        for param, data in self.param_data.items():
            data.setData([], [])
        for param, data in self.overlay_data.items():
            data.setData([], [])

    def updatePlots(self, data_cache, **kwargs):
        return
