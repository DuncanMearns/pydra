from PyQt5 import QtWidgets, QtCore


class SpinboxWidget(QtWidgets.QWidget):

    valueChanged = QtCore.pyqtSignal(int)

    def __init__(self, label, minVal=None, maxVal=None, suffix: str=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLayout(QtWidgets.QFormLayout())
        self.spinbox = QtWidgets.QSpinBox()
        if minVal is not None:
            self.spinbox.setMinimum(minVal)
        if maxVal is not None:
            self.spinbox.setMaximum(maxVal)
        if suffix is not None:
            self.spinbox.setSuffix(f" {suffix}")
        self.spinbox.valueChanged.connect(lambda val: self.valueChanged.emit(val))
        self.layout().addRow(f"{label}: ", self.spinbox)

    def setValue(self, val, emit=True):
        self.spinbox.setValue(val)
        if emit:
            self.valueChanged.emit(val)

    @property
    def value(self):
        return self.spinbox.value()


class DoubleSpinboxWidget(QtWidgets.QWidget):

    valueChanged = QtCore.pyqtSignal(float)

    def __init__(self, label, minVal = None, maxVal = None, suffix: str = None, dec=2, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLayout(QtWidgets.QFormLayout())
        self.spinbox = QtWidgets.QDoubleSpinBox()
        self.spinbox.setDecimals(dec)
        if minVal is not None:
            self.spinbox.setMinimum(minVal)
        if maxVal is not None:
            self.spinbox.setMaximum(maxVal)
        if suffix is not None:
            self.spinbox.setSuffix(f" {suffix}")
        self.spinbox.valueChanged.connect(lambda val: self.valueChanged.emit(val))
        self.layout().addRow(f"{label}: ", self.spinbox)

    def setValue(self, val, emit=True):
        self.spinbox.setValue(val)
        if emit:
            self.valueChanged.emit(val)

    @property
    def value(self):
        return self.spinbox.value()
