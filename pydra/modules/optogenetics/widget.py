from PyQt5 import QtWidgets, QtCore
from pydra.gui import ModuleWidget


class OptogeneticsWidget(ModuleWidget):

    plot = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Name
        self.setWidget(QtWidgets.QWidget())
        self.widget().setLayout(QtWidgets.QGridLayout())
        self.setMinimumHeight(250)
        # --------------
        # GUI components
        # --------------
        # Connection
        self.connection_widget = QtWidgets.QWidget()
        self.connection_widget.setLayout(QtWidgets.QVBoxLayout())
        button_widget = QtWidgets.QWidget()
        button_widget.setLayout(QtWidgets.QHBoxLayout())
        self.connect_button = QtWidgets.QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_to_laser)
        self.disconnect_button = QtWidgets.QPushButton("Disconnect")
        self.disconnect_button.setEnabled(False)
        self.disconnect_button.clicked.connect(self.disconnect_from_laser)
        button_widget.layout().addWidget(self.connect_button)
        button_widget.layout().addWidget(self.disconnect_button)
        self.connection_widget.layout().addWidget(button_widget)
        self.connected_text = QtWidgets.QLabel("Status: disconnected")
        self.connection_widget.layout().addWidget(self.connected_text, alignment=QtCore.Qt.AlignCenter)
        self.widget().layout().addWidget(self.connection_widget, 0, 0)
        divider = QtWidgets.QFrame()
        divider.setFrameStyle(divider.HLine | divider.Plain)
        self.widget().layout().addWidget(divider)
        # Laser status
        self.laser_state = 0
        self.status_widget = QtWidgets.QWidget()
        self.status_widget.setLayout(QtWidgets.QGridLayout())
        self.laser_button = QtWidgets.QPushButton("TOGGLE")
        self.laser_button.clicked.connect(self.toggle_laser)
        self.status_widget.layout().addWidget(self.laser_button, 0, 0, 1, 2, alignment=QtCore.Qt.AlignCenter)
        self.status_widget.layout().addWidget(QtWidgets.QLabel("LASER:"), 0, 2, 1, 1, alignment=QtCore.Qt.AlignRight)
        self.status_label = QtWidgets.QLabel("OFF")
        self.status_label.setFrameStyle(self.status_label.WinPanel | self.status_label.Sunken)
        self.default_style = self.status_label.styleSheet()
        self.status_widget.layout().addWidget(self.status_label, 0, 3, 1, 1, alignment=QtCore.Qt.AlignLeft)
        self.status_widget.setEnabled(False)
        self.widget().layout().addWidget(self.status_widget, 2, 0)
        divider = QtWidgets.QFrame()
        divider.setFrameStyle(divider.HLine | divider.Plain)
        self.widget().layout().addWidget(divider)

    def enterIdle(self):
        self.connection_widget.setEnabled(True)

    def enterRunning(self):
        self.connection_widget.setEnabled(False)

    @QtCore.pyqtSlot()
    def connect_to_laser(self):
        self.connect_button.setEnabled(False)
        self.disconnect_button.setEnabled(True)
        self.connected_text.setText("Status: connected")
        self.status_widget.setEnabled(True)
        self.send_event("connect")

    @QtCore.pyqtSlot()
    def disconnect_from_laser(self):
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.connected_text.setText("Status: disconnected")
        self.status_widget.setEnabled(False)
        self.send_event("disconnect")

    def toggle_laser(self):
        if self.laser_state:
            self.send_event("stimulation_off")
        else:
            self.send_event("stimulation_on")
        self.laser_state = int(not self.laser_state)

    def updatePlots(self, data, frame=None, **plotters):
        t, last_update = data["events"][-1]
        status = last_update["laser"]
        self.laser_state = status
        if status:
            self.status_label.setText("ON")
            self.status_label.setFrameStyle(self.status_label.WinPanel | self.status_label.Raised)
            self.status_label.setStyleSheet('background-color: cyan')
        else:
            self.status_label.setText("OFF")
            self.status_label.setFrameStyle(self.status_label.WinPanel | self.status_label.Sunken)
            self.status_label.setStyleSheet(self.default_style)
