import pyqtgraph as pg


class MainDisplayWidget(pg.GraphicsLayoutWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image = pg.ImageItem()
        self.plot = self.addPlot()
        self.plot.setMouseEnabled(False, False)
        self.plot.setAspectLocked()
        self.plot.hideAxis('bottom')
        self.plot.hideAxis('left')
        self.plot.addItem(self.image)
