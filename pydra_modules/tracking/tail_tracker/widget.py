from PyQt5 import QtWidgets, QtCore
from pydra.gui import ControlWidget, Plotter
from modules.cameras.widget import FramePlotter
from tailtracker.gui import TailInitializationWidget


class TailTrackerWidget(ControlWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLayout(QtWidgets.QVBoxLayout())
        # Create a button in the module control widget that opens a dialog window
        self.button = QtWidgets.QPushButton("Initialize tracker")
        self.button.clicked.connect(self.open_dialog)
        self.layout().addWidget(self.button)
        # Create a tail initialization dialog window
        self.dialog = TailInitializationWidget.dialog(None)
        self.dialog.widget.changeImage.connect(self.update_image)
        self.dialog.accepted.connect(self.initialize_worker)
        # Get parameters from the worker initialization
        params = kwargs.get("params", {})
        try:
            self.acquisition = params["acquisition_worker"]
        except KeyError:
            raise ValueError(f"An `acquisition_worker` must be set in the params dictionary of the {self.name} module.")
        self.last_image = None

    def open_dialog(self):
        self.update_image()
        self.dialog.show()

    @QtCore.pyqtSlot()
    def update_image(self):
        self.dialog.widget.new_image(self.last_image)

    def updatePlots(self, data_cache, **kwargs):
        # Get the acquisition plotter
        try:
            acquisition_cache = kwargs[self.acquisition]
        except KeyError:
            raise ValueError(f"The `acquisition_worker` in the params dictionary of the {self.name} module does not "
                             f"match the name of a worker in the Pydra network.")
        # Update the last image
        self.last_image = acquisition_cache.array  # get the current frame of the acquisition cache

    @QtCore.pyqtSlot()
    def initialize_worker(self):
        ret, params = self.dialog.get_params()
        if ret:
            points, n_points, kw = params
            self.send_event("initialize_tracker", points=points, n=n_points, **kw)

    def enterRunning(self):
        self.setEnabled(False)

    def enterIdle(self):
        self.setEnabled(True)


class TailPlotter(Plotter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addParamPlot("angle")

    def updatePlots(self, data_cache, **kwargs):
        t = data_cache.t
        angle = data_cache["angle"]
        self.updateParam("angle", t, angle)


class TailOverlay(FramePlotter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def updatePlots(self, data_cache, **kwargs):
        super().updatePlots(data_cache, **kwargs)
        tail_points = kwargs["tail"].array
        if len(tail_points.shape):
            self.updateOverlay("frame", *tail_points.T)
