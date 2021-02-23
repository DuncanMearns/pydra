from pydra.utilities import clock
import pyqtgraph as pg
from collections import deque
import numpy as np


class Plotter(pg.GraphicsLayoutWidget):

    def __init__(self, cachesize=50000, *args, **kwargs):
        super().__init__()
        self.cachesize = cachesize
        self.image_plots = {}
        self.images = {}
        self.overlay_data = {}
        self.param_plots = {}
        self.param_data = {}
        self.caches = {}

    def addImagePlot(self, name, **kwargs):
        # Create plot item
        plot = pg.PlotItem()
        plot.setMouseEnabled(False, False)
        plot.setAspectLocked()
        plot.hideAxis('bottom')
        plot.hideAxis('left')
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
        self.caches[name] = deque(maxlen=self.cachesize)
        self.addItem(plot)
        self.nextRow()

    def updateImage(self, name: str, image: np.ndarray):
        if image.shape and name in self.images:
            self.images[name].setImage(image[::-1].T)

    def updateOverlay(self, name: str, data: np.ndarray):
        if name in self.overlay_data:
            self.overlay_data[name].setData(data)

    def updateParam(self, name: str, data: np.ndarray):
        if name in self.param_data:
            self.caches[name].extend(data)
            show = np.array(self.caches[name])
            self.param_data[name].setData(show)

    def update(self, data: dict):
        t = np.array(data.get("time", [])) - clock.t0
        for param, vals in data.get("data", {}).items():
            self.updateParam(param, np.array([t, vals]).T)

    def clear_data(self):
        for param, cache in self.caches.items():
            cache.clear()
            self.param_data[param].setData([], [])
        for param, data in self.overlay_data.items():
            data.setData([], [])

    def set_cachesize(self, size):
        self.cachesize = size
        for param in self.caches.keys():
            self.caches[param] = deque(maxlen=self.cachesize)
