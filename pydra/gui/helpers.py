from PyQt5 import QtWidgets, QtCore
from collections import OrderedDict


class SignalProxy(QtCore.QObject):
    """QObject containing a signal that can be accessed by multiple different classes."""
    signal = QtCore.pyqtSignal()

    def emit(self):
        self.signal.emit()

    def connect(self, slot):
        self.signal.connect(slot)


class UnitWidget(QtWidgets.QWidget):

    valueChanged = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setLayout(QtWidgets.QHBoxLayout())
        self.units = OrderedDict()
        self._function = lambda x: x
        # Spinbox
        self.spinbox = QtWidgets.QSpinBox()
        self.spinbox.valueChanged.connect(self.recompute_value)
        # Dropdown
        self.dropdown = QtWidgets.QComboBox()
        self.dropdown.currentTextChanged.connect(self.change_unit)
        # Add to layout
        self.layout().addWidget(self.spinbox)
        self.layout().addWidget(self.dropdown)

    @property
    def value(self):
        """Access the real value stored by the widget."""
        t = self.spinbox.value()
        return self._function(t)

    @QtCore.pyqtSlot(int)
    def recompute_value(self, i):
        self.valueChanged.emit(self.value)

    @QtCore.pyqtSlot(str)
    def change_unit(self, unit):
        unit_dict = self.units[unit]
        # Update the function used to compute the value
        self._function = unit_dict["function"]
        # Update the spinbox
        minval = unit_dict["min"]
        maxval = unit_dict["max"]
        self.spinbox.setMinimum(minval)
        self.spinbox.setMaximum(maxval)
        # Ensure new value is emitted
        self.recompute_value(self.spinbox.value())

    def addUnit(self, name: str, func: callable, minval: int = 0, maxval: int = 999):
        self.units[name] = {"function": func,
                            "min": minval,
                            "max": maxval}
        self.dropdown.addItem(name)
        self.dropdown.setCurrentIndex(0)

    def setValue(self, val):
        self.spinbox.setValue(val)


class TimeUnitWidget(UnitWidget):
    """UnitWidget with value stored in milliseconds."""

    def addMilliseconds(self, **kwargs):
        self.addUnit("ms", self.milliseconds, **kwargs)

    def addSeconds(self, **kwargs):
        self.addUnit("s", self.seconds, **kwargs)

    def addMinutes(self, **kwargs):
        self.addUnit("min", self.minutes, **kwargs)

    @staticmethod
    def milliseconds(t):
        return t

    @staticmethod
    def seconds(t):
        return t * 1000

    @staticmethod
    def minutes(t):
        return t * 60_000


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
        self.spinbox.valueChanged.connect(self.valueChanged)
        self.layout().addRow(f"{label}: ", self.spinbox)

    def setValue(self, val, emit=True):
        if not emit:
            self.spinbox.blockSignals(True)
        self.spinbox.setValue(val)
        self.spinbox.blockSignals(False)

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
