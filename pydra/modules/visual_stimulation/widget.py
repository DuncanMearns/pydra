from pydra.gui import ModuleWidget
from PyQt5 import QtWidgets, QtCore


class VisualStimulationWidget(ModuleWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create widget and layout
        self.setWidget(QtWidgets.QWidget())
        self.widget().setLayout(QtWidgets.QVBoxLayout())
        self.widget().layout().setAlignment(QtCore.Qt.AlignTop)
        # Create buttons
        self.start_button = QtWidgets.QPushButton("RUN")
        self.stop_button = QtWidgets.QPushButton("INTERRUPT")
        self.widget().layout().addWidget(self.start_button)
        self.widget().layout().addWidget(self.stop_button)
        # Connections
        self.start_button.clicked.connect(self.run_stimulus)
        self.stop_button.clicked.connect(self.interrupt_stimulus)

    @QtCore.pyqtSlot()
    def run_stimulus(self):
        self.send_event("run_stimulus")

    @QtCore.pyqtSlot()
    def interrupt_stimulus(self):
        self.send_event("interrupt")
