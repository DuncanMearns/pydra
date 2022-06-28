from PyQt5 import QtWidgets, QtCore

from ..dynamic import Stateful
from ..helpers import TimeUnitWidget
from .protocol_builder import ProtocolBuilder


class ProtocolTab(Stateful, QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        # Layout
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        # -----------
        # REPETITIONS
        # -----------
        self.reps_widget = QtWidgets.QWidget()
        self.reps_widget.setLayout(QtWidgets.QHBoxLayout())
        self.reps_widget.layout().setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        # Repetitions
        self.reps_label = QtWidgets.QLabel("N reps:")
        self.reps_label.setToolTip("Number of repetitions of the protocol within a trial")
        self.reps_spinbox = QtWidgets.QSpinBox()
        self.reps_spinbox.setMinimum(1)
        self.reps_spinbox.setMaximum(999)
        self.reps_spinbox.setValue(1)
        # Interval
        self.interval_label = QtWidgets.QLabel("Interval:")
        self.interval_label.setToolTip("Time between protocol repetitions")
        self.interval_widget = TimeUnitWidget()
        self.interval_widget.addMilliseconds(minval=0, maxval=60_000)
        self.interval_widget.addSeconds(minval=0, maxval=600)
        self.interval_widget.addMinutes(minval=0, maxval=300)
        # Add to layout
        self.reps_widget.layout().addWidget(self.reps_label)
        self.reps_widget.layout().addWidget(self.reps_spinbox)
        self.reps_widget.layout().addWidget(self.interval_label)
        self.reps_widget.layout().addWidget(self.interval_widget)
        self.layout().addWidget(self.reps_widget)
        # -------
        # DIVIDER
        # -------
        self.layout().addWidget(self.divider())
        # -------
        # BUILDER
        # -------
        self.builder_widget = ProtocolBuilder(("hello_world",))
        self.layout().addWidget(self.builder_widget)
        # -----------
        # SAVE / LOAD
        # -----------
        self.layout().addWidget(self.divider())
        self.SAVE = QtWidgets.QPushButton("SAVE")
        self.LOAD = QtWidgets.QPushButton("LOAD")
        self.CLEAR = QtWidgets.QPushButton("CLEAR")
        self.buttons_container = QtWidgets.QWidget()
        self.buttons_container.setLayout(QtWidgets.QHBoxLayout())
        self.buttons_container.layout().addWidget(self.SAVE)
        self.buttons_container.layout().addWidget(self.LOAD)
        self.buttons_container.layout().addWidget(self.CLEAR)
        self.layout().addWidget(self.buttons_container)

    @staticmethod
    def divider():
        divider = QtWidgets.QFrame()
        divider.setFrameStyle(divider.HLine | divider.Plain)
        divider.setLineWidth(1)
        return divider


class TimedTab(Stateful, QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.setLayout(QtWidgets.QGridLayout())
        self.layout().setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        # Checkbox
        self.freerun_checkbox = QtWidgets.QCheckBox("Free-running")
        self.freerun_checkbox.stateChanged.connect(self.change_freerun)
        # Label
        self.duration_label = QtWidgets.QLabel("Duration:")
        # Time
        self.duration_widget = TimeUnitWidget()
        self.duration_widget.addSeconds(minval=1)
        self.duration_widget.addMinutes(minval=1)
        # Add to layout
        self.layout().addWidget(self.freerun_checkbox, 0, 0, 1, 2)
        self.layout().addWidget(self.duration_label, 1, 0, 1, 1)
        self.layout().addWidget(self.duration_widget, 1, 1, 1, 1)

    @QtCore.pyqtSlot(int)
    def change_freerun(self, state):
        if state:  # checked
            self.duration_label.setVisible(False)
            self.duration_widget.setVisible(False)
        else:  # not checked
            self.duration_label.setVisible(True)
            self.duration_widget.setVisible(True)


class TrialStructureWidget(Stateful, QtWidgets.QGroupBox):

    def __init__(self, triggers=()):
        super().__init__("Trial structure")
        self.triggers = triggers
        # Layout
        self.setLayout(QtWidgets.QGridLayout())
        self.layout().setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        # -----
        # START
        # -----
        # Start label
        self.start_label = QtWidgets.QLabel("START RECORDING")
        self.start_label.setFrameShape(QtWidgets.QFrame.Panel)
        self.start_label.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.start_label.setLineWidth(2)
        # Start trigger
        self.start_trigger_check = QtWidgets.QCheckBox("triggered")
        self.start_trigger_dropdown = QtWidgets.QComboBox()
        self.start_trigger_dropdown.addItems(self.triggers)
        self.start_trigger_dropdown.setEnabled(False)
        # Add to layout
        self.layout().addWidget(self.start_label, 0, 0)
        self.layout().addWidget(self.start_trigger_check, 0, 1)
        self.layout().addWidget(self.start_trigger_dropdown, 0, 2)
        # --------
        # PROTOCOL
        # --------
        self.timed_widget = TimedTab()
        self.protocol_widget = ProtocolTab()
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.addTab(self.timed_widget, "Timed")
        self.tab_widget.addTab(self.protocol_widget, "Protocol")
        self.layout().addWidget(self.tab_widget, 1, 0, 1, 3)
        # ----
        # STOP
        # ----
        # Stop label
        self.stop_label = QtWidgets.QLabel("STOP RECORDING")
        self.stop_label.setFrameShape(QtWidgets.QFrame.Panel)
        self.stop_label.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.stop_label.setLineWidth(2)
        # Stop trigger
        self.stop_trigger_check = QtWidgets.QCheckBox("triggered")
        self.stop_trigger_dropdown = QtWidgets.QComboBox()
        self.stop_trigger_dropdown.addItems(self.triggers)
        self.stop_trigger_dropdown.setEnabled(False)
        # Add to layout
        self.layout().addWidget(self.stop_label, 2, 0)
        self.layout().addWidget(self.stop_trigger_check, 2, 1)
        self.layout().addWidget(self.stop_trigger_dropdown, 2, 2)
