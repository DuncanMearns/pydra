from PyQt5 import QtWidgets, QtCore
from pydra.gui import ControlWidget, Plotter
from pydra.gui.helpers import SpinboxWidget, DoubleSpinboxWidget


class ParameterGroupBox(QtWidgets.QGroupBox):

    param_changed = QtCore.pyqtSignal(dict)

    def __init__(self, **kwargs):
        super().__init__()
        self.setLayout(QtWidgets.QHBoxLayout())
        self.widget = QtWidgets.QWidget()
        self.widget.setLayout(QtWidgets.QGridLayout())
        self.param_editors = []
        self.layout().addWidget(self.widget)

    def addSpinBox(self, name, minVal, maxVal, default=None, row=0, col=0, **kwargs):
        self._add_param(SpinboxWidget, name, minVal, maxVal, default, row, col, **kwargs)

    def addDoubleSpinBox(self, name, minVal, maxVal, default=None, row=0, col=0, **kwargs):
        self._add_param(DoubleSpinboxWidget, name, minVal, maxVal, default, row, col, **kwargs)

    def _add_param(self, widget_type, name, minVal, maxVal, default=None, row=0, col=0, **kwargs):
        param_editor = widget_type(name, minVal=minVal, maxVal=maxVal, **kwargs)
        param_editor.spinbox.setKeyboardTracking(False)
        if default is not None:
            param_editor.setValue(default, emit=False)
        param_editor.valueChanged.connect(self.confirm_changes)
        self.widget.layout().addWidget(param_editor, row, col, alignment=QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.param_editors.append(param_editor)

    @property
    def values(self):
        return [editor.value for editor in self.param_editors]

    @property
    def param_dict(self):
        return {}

    def set_values(self, *args):
        for editor, val in zip(self.param_editors, args):
            if val is not None:
                editor.setValue(val, emit=False)

    @QtCore.pyqtSlot()
    def confirm_changes(self):
        self.param_changed.emit(self.param_dict)


class FrameSizeWidget(ParameterGroupBox):

    def __init__(self, **kwargs):
        super().__init__()
        width, height = kwargs.get("frame_size", (None, None))
        min_width, min_height = kwargs.get("min_size", (1, 1))
        max_width, max_height = kwargs.get("max_size", (999, 999))
        self.addSpinBox("Width", min_width, max_width, width, 0, 0)
        self.addSpinBox("Height", min_height, max_height, height, 0, 1)

    @property
    def param_dict(self):
        w, h = self.values
        return {"frame_size": (w, h)}


class FrameRateWidget(ParameterGroupBox):

    def __init__(self, **kwargs):
        super().__init__()
        frame_rate = kwargs.get("frame_rate", None)
        min_fps = kwargs.get("min_frame_rate", 1.0)
        max_fps = kwargs.get("max_frame_rate", 500.)
        self.addDoubleSpinBox("Frame rate", min_fps, max_fps, frame_rate, 0, 0, suffix="fps")

    @property
    def param_dict(self):
        fps, *args = self.values
        return {"frame_rate": fps}


class ExposureWidget(ParameterGroupBox):

    def __init__(self, **kwargs):
        super().__init__()
        # Exposure
        exposure = kwargs.get("exposure", None)
        min_exposure = kwargs.get("min_exposure", 0.01)
        max_exposure = kwargs.get("max_exposure", 1000)
        self.addDoubleSpinBox("Exposure", min_exposure, max_exposure, exposure, 0, 0, dec=3, suffix="ms")
        # Gain
        gain = kwargs.get("gain", None)
        min_gain = kwargs.get("min_gain", 1.0)
        max_gain = kwargs.get("max_gain", 4.0)
        self.addDoubleSpinBox("Gain", min_gain, max_gain, gain, 1, 0)

    @property
    def param_dict(self):
        exposure, gain = self.values
        exposure = int(exposure * 1000)  # convert ms to us
        return {"exposure": exposure, "gain": gain}


class CameraWidget(ControlWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setSpacing(0)
        # Frame size
        self.frame_size_widget = FrameSizeWidget(**kwargs.get("params", {}))
        self.frame_size_widget.param_changed.connect(self.param_changed)
        self.layout().addWidget(self.frame_size_widget, alignment=QtCore.Qt.AlignTop)
        # Frame rate
        self.frame_rate_widget = FrameRateWidget(**kwargs.get("params", {}))
        self.frame_rate_widget.param_changed.connect(self.param_changed)
        self.layout().addWidget(self.frame_rate_widget, alignment=QtCore.Qt.AlignTop)
        # Exposure
        self.exposure_widget = ExposureWidget(**kwargs.get("params", {}))
        self.exposure_widget.param_changed.connect(self.param_changed)
        self.layout().addWidget(self.exposure_widget, alignment=QtCore.Qt.AlignTop)

    def set_params(self, **kwargs):
        if "frame_size" in kwargs:
            self.frame_size_widget.set_values(*kwargs["frame_size"])
        if "frame_rate" in kwargs:
            self.frame_rate_widget.set_values(kwargs["frame_rate"])
        exposure = kwargs.get("exposure", None)
        try:
            exposure = exposure / 1000.
        except TypeError:
            pass
        gain = kwargs.get("gain", None)
        if (exposure is not None) or (gain is not None):
            self.exposure_widget.set_values(exposure, gain)

    @QtCore.pyqtSlot(dict)
    def param_changed(self, new_params):
        self.send_event("set_params", params=new_params)

    def enterRunning(self):
        self.setEnabled(False)

    def enterIdle(self):
        self.setEnabled(True)

    def dynamicUpdate(self):
        try:
            new_events = self.cache.events
            if len(new_events):
                t, new_params = new_events[-1]
                self.cache.clear()
                self.set_params(**new_params)
        except AttributeError:
            return


class FramePlotter(Plotter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addImagePlot("frame", pen=None, symbol='o')

    def dynamicUpdate(self):
        try:
            self.updateImage("frame", self.cache.frame)
        except AttributeError:
            return
