from ..core import Plugin
from ..gui import PluginWidget
from .cameras import PikeCamera as CameraWorker
from PyQt5 import QtCore, QtWidgets, QtGui


class ValueEditor(QtWidgets.QLineEdit):

    valueChanged = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setPlaceholderText(self.text())
        self.editingFinished.connect(self.change_value)

    @QtCore.pyqtSlot()
    def change_value(self):
        self.setPlaceholderText(self.text())
        self.valueChanged.emit()


class CameraWidget(PluginWidget):

    def __init__(self, plugin, *args, **kwargs):
        super().__init__(plugin, *args, **kwargs)
        # Name
        self.setWindowTitle('Camera')
        # Frame width
        self.frame_width_editor = ValueEditor(str(self.plugin.frame_width))
        self.frame_width_editor.valueChanged.connect(self.param_changed)
        self.widget().layout().addWidget(QtWidgets.QLabel('Width:'), 0, 0, alignment=QtCore.Qt.AlignLeft)
        self.widget().layout().addWidget(self.frame_width_editor, 0, 1, alignment=QtCore.Qt.AlignLeft)
        # Frame height
        self.frame_height_editor = ValueEditor(str(self.plugin.frame_height))
        self.frame_height_editor.valueChanged.connect(self.param_changed)
        self.widget().layout().addWidget(QtWidgets.QLabel('Height:'), 0, 2, alignment=QtCore.Qt.AlignLeft)
        self.widget().layout().addWidget(self.frame_height_editor, 0, 3, alignment=QtCore.Qt.AlignLeft)
        # Frame rate
        self.frame_rate_editor = ValueEditor(str(self.plugin.frame_rate))
        self.frame_rate_editor.valueChanged.connect(self.param_changed)
        self.widget().layout().addWidget(QtWidgets.QLabel('Frame rate:'), 1, 0, alignment=QtCore.Qt.AlignLeft)
        self.widget().layout().addWidget(self.frame_rate_editor, 1, 1, alignment=QtCore.Qt.AlignLeft)
        # Exposure
        self.exposure_editor = ValueEditor(str(self.plugin.exposure))
        self.exposure_editor.valueChanged.connect(self.param_changed)
        self.widget().layout().addWidget(QtWidgets.QLabel('Exposure:'), 2, 0, alignment=QtCore.Qt.AlignLeft)
        self.widget().layout().addWidget(self.exposure_editor, 2, 1, alignment=QtCore.Qt.AlignLeft)
        # Gain
        self.gain_editor = ValueEditor(str(self.plugin.gain))
        self.gain_editor.valueChanged.connect(self.param_changed)
        self.widget().layout().addWidget(QtWidgets.QLabel('Gain:'), 2, 2, alignment=QtCore.Qt.AlignLeft)
        self.widget().layout().addWidget(self.gain_editor, 2, 3, alignment=QtCore.Qt.AlignLeft)
        # Set validators
        self.int_editors = (self.frame_width_editor, self.frame_height_editor, self.exposure_editor, self.gain_editor)
        for editor in self.int_editors:
            editor.setValidator(QtGui.QIntValidator())
        self.frame_rate_editor.setValidator(QtGui.QDoubleValidator(decimals=2))
        self.param_changed()  # call this to ensure saver is properly updated

    @QtCore.pyqtSlot()
    def param_changed(self):
        width, height, exposure, gain = (int(editor.text()) for editor in self.int_editors)
        frame_rate = float(self.frame_rate_editor.text())
        new_params = dict(frame_size=(width, height), frame_rate=frame_rate, exposure=exposure, gain=gain)
        self.plugin.change_params(new_params)

    def idle(self):
        self.setEnabled(True)

    def live(self):
        self.setEnabled(False)

    def record(self):
        self.setEnabled(False)


class PikeCamera(Plugin):

    name = 'PikeCamera'
    worker = CameraWorker
    widget = CameraWidget

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params['frame_size'] = (340, 240)
        self.params['frame_rate'] = 250.
        self.params['exposure'] = 2695
        self.params['gain'] = 18

    def change_params(self, new):
        self.params.update(new)
        self.paramsChanged.emit(self.name, new)

    @property
    def frame_width(self):
        return self.params['frame_size'][0]

    @property
    def frame_height(self):
        return self.params['frame_size'][1]

    @property
    def exposure(self):
        return self.params['exposure']

    @property
    def gain(self):
        return self.params['gain']

    @property
    def frame_rate(self):
        return self.params['frame_rate']
