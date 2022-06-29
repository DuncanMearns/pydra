from pydra.gui import Plotter


class FramePlotter(Plotter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addImagePlot("frame", pen=None, symbol='o')

    def dynamicUpdate(self):
        try:
            self.updateImage("frame", self.cache.frame)
        except AttributeError:
            return
