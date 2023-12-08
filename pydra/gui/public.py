from .dynamic import DynamicUpdate
from .state_machine import Stateful

from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import numpy as np

pg.setConfigOption("imageAxisOrder", "row-major")


__all__ = ("ControlWidget", "Plotter")


class ControlWidget(DynamicUpdate, Stateful, QtWidgets.QWidget):
    """Base class for user-defined control widgets for interfacing with Pydra workers. Has access to experiment state
    and associated attributes, and may be dynamically updated with data from the Pydra network via the dynamicUpdate
    method.

    Parameters
    ----------
    name : str
        Name of the associated Pydra worker.
    params : dict
        Dictionary of parameters specified in the Pydra config that were passed to the worker at initialization.
    *args
    **kwargs
    """

    widgetEvent = QtCore.pyqtSignal(str, str, dict)  # name, event, kwargs

    def __init__(self, name, *args, params=None, **kwargs):
        super().__init__()
        self.name = name
        self.params = params or {}

    def on_start(self):
        """Called once when GUI is initialized. Override in subclasses."""
        return

    def send_event(self, event_name, **kwargs):
        """Emits a signal that sends an event to the Pydra network.

        Parameters
        ----------
        event_name : str
            The name of the event to transmit to the Pydra network.
        **kwargs
            Named keyword arguments associated with the event.
        """
        self.widgetEvent.emit(self.name, event_name, kwargs)


class Plotter(DynamicUpdate, Stateful, pg.GraphicsLayoutWidget):
    """Base class for user-defined plotter widgets that show incoming data from Pydra. Has access to experiment state
    and associated attributes, and may be dynamically updated with data from the Pydra network via the dynamicUpdate
    method.

    Parameters
    ----------
    name : str
        Name of the associated Pydra worker.
    params : dict
        Dictionary of parameters specified in the Pydra config that were passed to the worker at initialization.
    *args
    **kwargs
    """

    def __init__(self, name, *args, params=None, **kwargs):
        super().__init__()
        self.name = name
        self.params = params
        self.image_plots = {}
        self.images = {}
        self.overlay_data = {}
        self.param_plots = {}
        self.param_data = {}

    def addImagePlot(self, name, **kwargs):
        """Add an named image plot to the plotter."""
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
        """Add a named parameter plot to the plotter."""
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
        """Clear all data from the plotter."""
        for param, data in self.param_data.items():
            data.setData([], [])
        for param, data in self.overlay_data.items():
            data.setData([], [])
