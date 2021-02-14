from PyQt5 import QtWidgets, QtCore, QtGui
from pydra.gui import ModuleWidget
from pydra.gui.widgets import SpinboxWidget, DoubleSpinboxWidget


# class ValueEditor(QtWidgets.QLineEdit):
#
#     valueChanged = QtCore.pyqtSignal()
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.setPlaceholderText(self.text())
#         self.editingFinished.connect(self.change_value)
#
#     @QtCore.pyqtSlot()
#     def change_value(self):
#         self.setPlaceholderText(self.text())
#         self.valueChanged.emit()


class FrameSizeWidget(QtWidgets.QGroupBox):

    param_changed = QtCore.pyqtSignal(str, tuple)

    def __init__(self, **kwargs):
        super().__init__("Frame size")
        self.setLayout(QtWidgets.QHBoxLayout())
        width, height = kwargs.get("frame_size", (None, None))
        min_width, min_height = kwargs.get("min_size", (1, 1))
        max_width, max_height = kwargs.get("max_size", (999, 999))
        # Frame width
        self.frame_width_editor = SpinboxWidget("Width", minVal=min_width, maxVal=max_width)
        if width is not None:
            self.frame_width_editor.setValue(width, emit=False)
        self.frame_width_editor.valueChanged.connect(self.changed)
        self.layout().addWidget(self.frame_width_editor, alignment=QtCore.Qt.AlignLeft)
        # Frame height
        self.frame_height_editor = SpinboxWidget("Height", minVal=min_height, maxVal=max_height)
        if height is not None:
            self.frame_height_editor.setValue(height, emit=False)
        self.frame_height_editor.valueChanged.connect(self.changed)
        self.layout().addWidget(self.frame_height_editor, alignment=QtCore.Qt.AlignLeft)

    @QtCore.pyqtSlot(int)
    def changed(self, val):
        width = self.frame_width_editor.value
        height = self.frame_height_editor.value
        self.param_changed.emit("frame_size", (width, height))


class FrameRateWidget(QtWidgets.QGroupBox):

    param_changed = QtCore.pyqtSignal(str, object)

    def __init__(self, **kwargs):
        super().__init__("Frame rate")
        self.setLayout(QtWidgets.QHBoxLayout())
        frame_rate = kwargs.get("frame_rate", None)
        min_fps = kwargs.get("min_frame_rate", 1.0)
        max_fps = kwargs.get("max_frame_rate", 500.)
        # Frame rate
        self.editor = DoubleSpinboxWidget("Frame rate", minVal=min_fps, maxVal=max_fps, suffix="fps")
        if frame_rate is not None:
            self.editor.setValue(frame_rate, emit=False)
        self.editor.valueChanged.connect(self.changed)
        self.layout().addWidget(self.editor, alignment=QtCore.Qt.AlignLeft)

    @QtCore.pyqtSlot(float)
    def changed(self, val):
        self.param_changed.emit("frame_rate", val)


class ExposureWidget(QtWidgets.QGroupBox):

    param_changed = QtCore.pyqtSignal(str, object)

    def __init__(self, **kwargs):
        super().__init__("Exposure")
        self.setLayout(QtWidgets.QVBoxLayout())
        # Exposure
        exposure = kwargs.get("exposure", None)
        min_exposure = kwargs.get("min_exposure", 1)
        max_exposure = kwargs.get("max_exposure", 1000)
        self.exposure_editor = SpinboxWidget("Exposure", minVal=min_exposure, maxVal=max_exposure, suffix="ms")
        if exposure is not None:
            self.exposure_editor.setValue(exposure, emit=False)
        self.exposure_editor.valueChanged.connect(self.change_exposure)
        self.layout().addWidget(self.exposure_editor, alignment=QtCore.Qt.AlignLeft)
        # Gain
        gain = kwargs.get("gain", None)
        min_gain = kwargs.get("min_gain", 1.0)
        max_gain = kwargs.get("max_gain", 4.0)
        self.gain_editor = DoubleSpinboxWidget("Gain", minVal=min_gain, maxVal=max_gain)
        if gain is not None:
            self.gain_editor.setValue(gain, emit=False)
        self.gain_editor.valueChanged.connect(self.change_gain)
        self.layout().addWidget(self.gain_editor, alignment=QtCore.Qt.AlignLeft)

    @QtCore.pyqtSlot(int)
    def change_exposure(self, val):
        self.changed("exposure", val)

    @QtCore.pyqtSlot(float)
    def change_gain(self, val):
        self.changed("gain", val)

    def changed(self, param, val):
        self.param_changed.emit(param, val)


class CameraWidget(ModuleWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWidget(QtWidgets.QWidget())
        self.widget().setLayout(QtWidgets.QVBoxLayout())
        params = kwargs.get("params", {})
        # Frame size
        self.frame_size_widget = FrameSizeWidget(**params)
        self.frame_size_widget.param_changed.connect(self.param_changed)
        self.widget().layout().addWidget(self.frame_size_widget)
        # Frame rate
        self.frame_rate_widget = FrameRateWidget(**params)
        self.frame_rate_widget.param_changed.connect(self.param_changed)
        self.widget().layout().addWidget(self.frame_rate_widget)
        # Exposure
        self.exposure_widget = ExposureWidget(**params)
        self.exposure_widget.param_changed.connect(self.param_changed)
        self.widget().layout().addWidget(self.exposure_widget)
        # # Set validators
        # self.int_editors = (self.frame_width_editor, self.frame_height_editor, self.exposure_editor, self.gain_editor)
        # for editor in self.int_editors:
        #     editor.setValidator(QtGui.QIntValidator())
        # self.frame_rate_editor.setValidator(QtGui.QDoubleValidator(decimals=2))
        # self.param_changed()  # call this to ensure saver is properly updated

    @QtCore.pyqtSlot(str, object)
    def param_changed(self, param, new_val):
        new_params = {param: new_val}
        self.send_event("set_params", **new_params)
