from PyQt5 import QtWidgets, QtCore
from pydra.gui import ModuleWidget
from tailtracker.gui import TailInitializationWidget


class TailTrackerWidget(ModuleWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWidget(QtWidgets.QWidget())
        self.widget().setLayout(QtWidgets.QVBoxLayout())
        # Create a button in the module control widget that opens a dialog window
        self.button = QtWidgets.QPushButton("Initialize tracker")
        self.button.clicked.connect(self.open_dialog)
        self.widget().layout().addWidget(self.button)
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

    def create_plotter(self, *args, **kwargs):
        super().create_plotter(*args, **kwargs)
        self.plotter.addParamPlot("angle")
        self.plotter.set_cachesize(5000)

    def open_dialog(self):
        self.update_image()
        self.dialog.show()

    @QtCore.pyqtSlot()
    def update_image(self):
        self.dialog.widget.new_image(self.last_image)

    def updatePlots(self, data, frame=None, **plotters):
        self.plotter.update(data, exclude=("points",))
        # Get the acquisition plotter
        try:
            acquisition_plotter = plotters[self.acquisition]
        except KeyError:
            raise ValueError(f"The `acquisition_worker` in the params dictionary of the {self.name} module does not "
                             f"match the name of a worker in the Pydra network.")
        # Update the last image
        img = acquisition_plotter.images["frame"].image  # get the current frame of the acquisition plotter
        self.last_image = img
        # Track the last image and add overlay
        angle = self.dialog.widget.tracker.track(self.last_image)
        if angle is not None:
            points = self.dialog.widget.tracker.points
            x, y = zip(*points)
            acquisition_plotter.overlay_data["frame"].setData(x, y)

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
