from PyQt5 import QtWidgets, QtCore, QtGui
from pydra.gui import ModuleWidget


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


class CameraWidget(ModuleWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Name
        self.setWidget(QtWidgets.QWidget())
        self.widget().setLayout(QtWidgets.QGridLayout())
        # Frame width
        self.frame_width_editor = ValueEditor()
        self.frame_width_editor.valueChanged.connect(self.param_changed)
        self.widget().layout().addWidget(QtWidgets.QLabel('Width:'), 0, 0, alignment=QtCore.Qt.AlignLeft)
        self.widget().layout().addWidget(self.frame_width_editor, 0, 1, alignment=QtCore.Qt.AlignLeft)
        # Frame height
        self.frame_height_editor = ValueEditor()
        self.frame_height_editor.valueChanged.connect(self.param_changed)
        self.widget().layout().addWidget(QtWidgets.QLabel('Height:'), 0, 2, alignment=QtCore.Qt.AlignLeft)
        self.widget().layout().addWidget(self.frame_height_editor, 0, 3, alignment=QtCore.Qt.AlignLeft)
        # Frame rate
        self.frame_rate_editor = ValueEditor()
        self.frame_rate_editor.valueChanged.connect(self.param_changed)
        self.widget().layout().addWidget(QtWidgets.QLabel('Frame rate:'), 1, 0, alignment=QtCore.Qt.AlignLeft)
        self.widget().layout().addWidget(self.frame_rate_editor, 1, 1, alignment=QtCore.Qt.AlignLeft)
        # Exposure
        self.exposure_editor = ValueEditor()
        self.exposure_editor.valueChanged.connect(self.param_changed)
        self.widget().layout().addWidget(QtWidgets.QLabel('Exposure:'), 2, 0, alignment=QtCore.Qt.AlignLeft)
        self.widget().layout().addWidget(self.exposure_editor, 2, 1, alignment=QtCore.Qt.AlignLeft)
        # Gain
        self.gain_editor = ValueEditor()
        self.gain_editor.valueChanged.connect(self.param_changed)
        self.widget().layout().addWidget(QtWidgets.QLabel('Gain:'), 2, 2, alignment=QtCore.Qt.AlignLeft)
        self.widget().layout().addWidget(self.gain_editor, 2, 3, alignment=QtCore.Qt.AlignLeft)
        # Set validators
        self.int_editors = (self.frame_width_editor, self.frame_height_editor, self.exposure_editor, self.gain_editor)
        for editor in self.int_editors:
            editor.setValidator(QtGui.QIntValidator())
        self.frame_rate_editor.setValidator(QtGui.QDoubleValidator(decimals=2))
        # self.param_changed()  # call this to ensure saver is properly updated

    @QtCore.pyqtSlot()
    def param_changed(self):
        width, height, exposure, gain = (int(editor.text()) for editor in self.int_editors)
        frame_rate = float(self.frame_rate_editor.text())
        new_params = dict(frame_size=(width, height), frame_rate=frame_rate, exposure=exposure, gain=gain)
        print(new_params)
    #     self.plugin.change_params(new_params)
