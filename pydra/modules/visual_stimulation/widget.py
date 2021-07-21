from pydra.gui import ControlWidget
from PyQt5 import QtWidgets, QtCore


class VisualStimulationWidget(ControlWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get stimulus file (if exists)
        params = kwargs.get("params", {})
        self.stimulus_file = str(params.get("stimulus_file", ""))
        # Create widget and layout
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setAlignment(QtCore.Qt.AlignTop)
        # Create buttons
        self.load_button = QtWidgets.QPushButton("Load")
        self.stimulus_label = QtWidgets.QLabel(self.stimulus_file)
        self.start_button = QtWidgets.QPushButton("RUN")
        self.start_button.setFixedHeight(50)
        self.stop_button = QtWidgets.QPushButton("INTERRUPT")
        self.layout().addWidget(self.load_button)
        self.layout().addWidget(self.stimulus_label)
        self.layout().addWidget(self.start_button)
        self.layout().addWidget(self.stop_button)
        # Connections
        self.load_button.clicked.connect(self.load_stimulus)
        self.start_button.clicked.connect(self.run_stimulus)
        self.stop_button.clicked.connect(self.interrupt_stimulus)

    @QtCore.pyqtSlot()
    def run_stimulus(self):
        self.send_event("run")

    @QtCore.pyqtSlot()
    def interrupt_stimulus(self):
        self.send_event("interrupt")

    @QtCore.pyqtSlot()
    def load_stimulus(self):
        filepath = QtWidgets.QFileDialog.getOpenFileName(self,
                                                         "Choose .py file containing a stimulus_list.",
                                                         self.stimulus_file,
                                                         filter="Stimulus file (*.py)")
        filepath = filepath[0]
        if filepath:
            self.stimulus_file = filepath
            self.stimulus_label.setText(self.stimulus_file)
            self.send_event("load", stimulus_file=filepath)

    def enterRunning(self):
        super().enterRunning()
        self.load_button.setEnabled(False)

    def enterIdle(self):
        super().enterIdle()
        self.load_button.setEnabled(True)
