from PyQt5 import QtWidgets, QtCore
from ..states import StateEnabled


class SpinboxWidget(QtWidgets.QWidget):

    def __init__(self, label, minVal=0, suffix: str=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLayout(QtWidgets.QFormLayout())
        self.spinbox = QtWidgets.QSpinBox()
        self.spinbox.setMinimum(minVal)
        if suffix is not None:
            self.spinbox.setSuffix(f" {suffix}")
        self.layout().addRow(f"{label}: ", self.spinbox)

    @property
    def value(self):
        return self.spinbox.value()


class ProtocolWidget(QtWidgets.QGroupBox, StateEnabled):

    editor_clicked = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__("Protocol", *args, **kwargs)
        self.initUI()

    def initUI(self):
        # Layout
        self.setLayout(QtWidgets.QHBoxLayout())
        # Current protocol
        self.protocol = None
        self.protocol_label = QtWidgets.QLabel("Free-running mode")
        self.layout().addWidget(self.protocol_label)
        # Editor button
        self.editor_button = QtWidgets.QPushButton("change")
        self.editor_button.clicked.connect(self.editProtocol)
        self.layout().addWidget(self.editor_button)
        # N repetitions
        self.n_repetitions = 1
        self.repetitions_widget = SpinboxWidget("Repetitions", minVal=1)
        self.layout().addWidget(self.repetitions_widget)
        # Interval
        self.interval = 0
        self.interval_widget = SpinboxWidget("Interval", suffix="s")
        self.layout().addWidget(self.interval_widget)
        # Protocol progress
        self.progress_label = QtWidgets.QLabel("")
        self.layout().addWidget(self.progress_label)

    def editProtocol(self):
        self.editor_clicked.emit()

    @property
    def value(self) -> (int, int):
        return self.repetitions_widget.value, self.interval_widget.value

    def update_protocol(self, name):
        self.protocol = name
        if name:
            self.protocol_label.setText(f"Current: {self.protocol}")
        else:
            self.protocol_label.setText("Free-running mode")

    def startRecord(self, i):
        self.progress_label.setText(f"Running protocol: {self.protocol} | Repetition: {i}/{self.n_repetitions}")

    def endRecord(self, i):
        self.progress_label.setText(f"Running protocol: {self.protocol} | Waiting...")

    def enterRunning(self):
        self.n_repetitions, self.interval = self.value
        self.progress_label.setText(f"Running protocol: {self.protocol}")
        super().enterRunning()

    def enterIdle(self):
        self.progress_label.setText(f"")
        super().enterIdle()
