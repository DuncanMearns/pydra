from pydra.gui import ControlWidget
from PyQt5 import QtWidgets, QtCore


class VisualStimulationWidget(ControlWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create widget and layout
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setAlignment(QtCore.Qt.AlignTop)
        # Create buttons
        self.start_button = QtWidgets.QPushButton("RUN")
        self.stop_button = QtWidgets.QPushButton("INTERRUPT")
        self.layout().addWidget(self.start_button)
        self.layout().addWidget(self.stop_button)
        # Connections
        self.start_button.clicked.connect(self.run_stimulus)
        self.stop_button.clicked.connect(self.interrupt_stimulus)

    @QtCore.pyqtSlot()
    def run_stimulus(self):
        self.send_event("run")

    @QtCore.pyqtSlot()
    def interrupt_stimulus(self):
        self.send_event("interrupt")
