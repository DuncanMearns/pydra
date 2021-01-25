from PyQt5 import QtWidgets
import pyqtgraph as pg
import numpy as np
from collections import deque
import time


class PlotterWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLayout(QtWidgets.QGridLayout())
        self.pipelines = {}

    def addPlotter(self, name, params):
        widget = PipelineWidget(name, params)
        self.pipelines[name] = widget
        j = self.layout().columnCount()
        self.layout().addWidget(widget, 0, j)

    def updatePlots(self, name, data, frame):
        self.pipelines[name].updatePlots(frame, **data)


class PipelineWidget(QtWidgets.QGroupBox):

    def __init__(self, name, params, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTitle(name)
        self.setLayout(QtWidgets.QGridLayout())
        self.w = pg.GraphicsLayoutWidget()
        self.layout().addWidget(self.w)
        self.params = params
        # self.setLayout(pg.GraphicsLayout())
        # Create image plot
        self.image_plot = self.w.addPlot(row=0, col=0)
        self.image_plot.setMouseEnabled(False, False)
        self.image_plot.setAspectLocked()
        self.image_plot.hideAxis('bottom')
        self.image_plot.hideAxis('left')
        self.image = pg.ImageItem()
        self.image_plot.addItem(self.image)
        # Create param plots
        self._plotters = {}
        self.plot_data = {}
        self.caches = {}
        self.t0 = time.time()
        for i, param in enumerate(self.params):
            param_plot = self.w.addPlot(row=i + 1, col=0, title=param)
            if len(self._plotters):
                param_plot.setXLink(self._plotters[list(self._plotters.keys())[0]])
            plot_data = param_plot.plot([], [])
            self._plotters[param] = param_plot
            self.caches[param] = deque(maxlen=10000)
            self.plot_data[param] = plot_data

    def updatePlots(self, frame, **kwargs):
        if frame.shape:
            self.image.setImage(frame)
        for worker, params in kwargs.items():
            x = np.array(params.get("time", [])) - self.t0
            for key, data in params.get("data", {}).items():
                data_name = ".".join([worker, key])
                try:
                    self.caches[data_name].extend(zip(x, data))
                    show_data = np.array(self.caches[data_name])
                    self.plot_data[data_name].setData(show_data[:, 0], show_data[:, 1])
                except KeyError:
                    pass
