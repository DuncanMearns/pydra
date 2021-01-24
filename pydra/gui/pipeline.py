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
        self.layout().addWidget(widget)

    def updatePlots(self, name, data, frame):
        self.pipelines[name].update(frame, **data)


class PipelineWidget(pg.GraphicsLayoutWidget):

    def __init__(self, name, params, *args, **kwargs):
        super().__init__(title=name, *args, **kwargs)
        self.params = params
        # Create image plot
        self.image = pg.ImageItem()
        self.image_plot = self.addPlot(row=0, col=0)
        self.image_plot.addItem(self.image)
        # Create param plots
        self._plotters = {}
        self.plot_data = {}
        self.caches = {}
        self.t0 = time.time()
        for i, param in enumerate(self.params):
            param_plot = self.addPlot(row=i + 1, col=0, title=param)
            if len(self._plotters):
                param_plot.setXLink(self._plotters[list(self._plotters.keys())[0]])
            plot_data = param_plot.plot([], [])
            self._plotters[param] = param_plot
            self.caches[param] = deque(maxlen=10000)
            self.plot_data[param] = plot_data

        # self.plot.setMouseEnabled(False, False)
        # self.plot.setAspectLocked()
        # self.plot.hideAxis('bottom')
        # self.plot.hideAxis('left')
        # self.plot.addItem(self.image)
        # # Frame rate estimate
        # self.fps_est = 0
        # self.t0 = np.array([0, 0])
        # self.fps_formatter = r'Frame rate: {}'
        # self.fps_text = pg.TextItem(self.fps_formatter.format(self.fps_est), anchor=(0, 0))
        # self.plot.addItem(self.fps_text)

    def update(self, frame, **kwargs):
        if len(frame):
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


            # print(data_names)
        #     print(worker, params)

        # last = args[-1]
        # # Update image
        # frame = last.frame
        # self.image.setImage(frame[::-1, :].T)
        # # Update frame rate
        # t1 = np.array([last.frame_number, last.timestamp])
        # dt = t1 - self.t0
        # self.fps_est = np.round(dt[0] / dt[1], 1)
        # self.fps_text.setText(self.fps_formatter.format(self.fps_est))
        # self.t0 = t1
