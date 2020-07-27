import pyqtgraph as pg
import numpy as np


class Plotter:

    def __init__(self, parent, name):
        self.parent = parent
        self.name = name

    @classmethod
    def add(cls, parent, name):
        parent.new_plot(name)
        return cls(parent, name)

    @property
    def plot(self):
        return self.parent.plots[self.name]

    def reset(self):
        return

    def update(self, *args):
        return


class MainPlotter(Plotter):

    def __init__(self, parent, *args):
        super().__init__(parent, "main")
        self.image = pg.ImageItem()
        self.plot.setMouseEnabled(False, False)
        self.plot.setAspectLocked()
        self.plot.hideAxis('bottom')
        self.plot.hideAxis('left')
        self.plot.addItem(self.image)
        # Frame rate estimate
        self.fps_est = 0
        self.t0 = np.array([0, 0])
        self.fps_formatter = r'Frame rate: {}'
        self.fps_text = pg.TextItem(self.fps_formatter.format(self.fps_est), anchor=(0, 0))
        self.plot.addItem(self.fps_text)

    def update(self, *args):
        last = args[-1]
        # Update image
        frame = last.frame
        self.image.setImage(frame[::-1, :].T)
        # Update frame rate
        t1 = np.array([last.frame_number, last.timestamp])
        dt = t1 - self.t0
        self.fps_est = np.round(dt[0] / dt[1], 1)
        self.fps_text.setText(self.fps_formatter.format(self.fps_est))
        self.t0 = t1


class MainDisplayWidget(pg.GraphicsLayoutWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plots = {}

    def new_plot(self, name):
        n_plots = len(self.plots)
        new = self.addPlot(n_plots, 0)
        self.plots[name] = new
