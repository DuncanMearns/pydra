from PyQt5 import QtCore, QtWidgets
from ...gui.widget import PluginWidget


class OptogeneticsWidget(PluginWidget):

    def __init__(self, plugin, *args, **kwargs):
        super().__init__(plugin, *args, **kwargs)
        # Name
        self.setWindowTitle('Optogenetics')
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
        self.disconnect_button = QtWidgets.QPushButton("Disconnect")
        self.disconnect_button.setEnabled(False)
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
        self.status_widget = QtWidgets.QWidget()
        self.status_widget.setLayout(QtWidgets.QGridLayout())
        self.laser_button = QtWidgets.QPushButton("TOGGLE")
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
        # Settings
        self.settings_widget = QtWidgets.QWidget()
        self.settings_widget.setLayout(QtWidgets.QGridLayout())
        self.settings_button = QtWidgets.QPushButton("Settings")
        self.settings_widget.layout().addWidget(self.settings_button)
        self.widget().layout().addWidget(self.settings_widget)
        # --------------
        # State handling
        # --------------
        self.stateMachine = QtCore.QStateMachine()
        # Connected / disconnected states
        self.connectedState = QtCore.QState()
        self.connectedState.entered.connect(self.connect_to_laser)
        self.connectedState.exited.connect(self.disconnect_from_laser)
        self.disconnectedState = QtCore.QState()
        self.disconnectedState.addTransition(self.connect_button.clicked, self.connectedState)
        self.connectedState.addTransition(self.disconnect_button.clicked, self.disconnectedState)
        # On/off states within connected state
        self.onState = QtCore.QState(self.connectedState)
        self.offState = QtCore.QState(self.connectedState)
        self.onState.entered.connect(self.laser_on)
        self.onState.exited.connect(self.laser_off)
        self.offState.addTransition(self.laser_button.clicked, self.onState)
        self.onState.addTransition(self.laser_button.clicked, self.offState)
        # Set initial states
        self.connectedState.setInitialState(self.offState)
        self.stateMachine.addState(self.connectedState)
        self.stateMachine.addState(self.disconnectedState)
        self.stateMachine.setInitialState(self.disconnectedState)
        self.stateMachine.start()

    def idle(self):
        self.connection_widget.setEnabled(True)

    def live(self):
        self.connection_widget.setEnabled(False)

    def record(self):
        self.connection_widget.setEnabled(False)

    @QtCore.pyqtSlot()
    def connect_to_laser(self):
        self.connect_button.setEnabled(False)
        self.disconnect_button.setEnabled(True)
        self.connected_text.setText("Status: connected")
        self.settings_widget.setEnabled(False)
        self.status_widget.setEnabled(True)
        self.plugin.connect_laser()

    @QtCore.pyqtSlot()
    def disconnect_from_laser(self):
        self.plugin.disconnect_laser()
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.connected_text.setText("Status: disconnected")
        self.settings_widget.setEnabled(True)
        self.status_widget.setEnabled(False)

    @QtCore.pyqtSlot()
    def laser_on(self):
        self.status_label.setText("ON")
        self.status_label.setFrameStyle(self.status_label.WinPanel | self.status_label.Raised)
        self.status_label.setStyleSheet('background-color: cyan')
        self.plugin.set_laser(True)

    @QtCore.pyqtSlot()
    def laser_off(self):
        self.status_label.setText("OFF")
        self.status_label.setFrameStyle(self.status_label.WinPanel | self.status_label.Sunken)
        self.status_label.setStyleSheet(self.default_style)
        self.plugin.set_laser(False)
