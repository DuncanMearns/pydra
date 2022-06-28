from pydra.gui import Plotter


class FramePlotter(Plotter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addImagePlot("frame", pen=None, symbol='o')

    def updatePlots(self, data_cache, **kwargs):
        self.updateImage("frame", data_cache.array)
