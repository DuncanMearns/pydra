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
        self.laser_button.clicked.connect(self.plugin.toggle_laser)
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
        self.protocol_widget = QtWidgets.QWidget()
        self.protocol_widget.setLayout(QtWidgets.QHBoxLayout())
        self.protocol_button = QtWidgets.QPushButton("Protocol")
        self.protocol_button.clicked.connect(self.create_protocol)
        self.protocol_widget.layout().addWidget(self.protocol_button)
        self.protocol_widget.setEnabled(False)
        self.widget().layout().addWidget(self.protocol_widget)

        # ==============
        # State handling
        # ==============
        # Top-level state machine
        self.stateMachine = QtCore.QStateMachine()
        # ------------------
        # Disconnected state
        self.disconnectedState = QtCore.QState()
        # Connected state (laser state & running state)
        self.connectedState = QtCore.QState(QtCore.QState.ParallelStates)
        self.laserState = QtCore.QState(self.connectedState)
        self.runningState = QtCore.QState(self.connectedState)
        self.connectedState.entered.connect(self.connect_to_laser)
        self.connectedState.exited.connect(self.disconnect_from_laser)
        # Transitions between disconnected and connected states
        self.disconnectedState.addTransition(self.connect_button.clicked, self.connectedState)
        self.connectedState.addTransition(self.disconnect_button.clicked, self.disconnectedState)
        # ---------------------
        # Laser state (on | off)
        self.onState = QtCore.QState(self.laserState)
        self.offState = QtCore.QState(self.laserState)
        self.onState.entered.connect(self.laser_on)
        self.onState.exited.connect(self.laser_off)
        # Transitions between on and off states
        self.offState.addTransition(self.plugin.laserOn, self.onState)
        self.onState.addTransition(self.plugin.laserOff, self.offState)
        # Set initial state
        self.laserState.setInitialState(self.offState)
        # ------------------------------
        # Running state (free | protocol)
        self.freeRunningState = QtCore.QState(self.runningState)
        self.protocolState = QtCore.QState(self.runningState)
        self.protocolState.entered.connect(self.protocol_running)
        self.protocolState.exited.connect(self.free_running)
        # Transitions between free-running and protocol states
        self.freeRunningState.addTransition(self.plugin.protocolStarted, self.protocolState)
        self.protocolState.addTransition(self.plugin.protocolFinished, self.freeRunningState)
        # Set initial state
        self.runningState.setInitialState(self.freeRunningState)
        # ------------------
        # Start state machine
        self.stateMachine.addState(self.connectedState)
        self.stateMachine.addState(self.disconnectedState)
        self.stateMachine.setInitialState(self.disconnectedState)
        self.stateMachine.start()

    def idle(self):
        self.connection_widget.setEnabled(True)
        # self.protocol_widget.setEnabled(True)

    def live(self):
        self.connection_widget.setEnabled(False)
        # self.protocol_widget.setEnabled(True)

    def record(self):
        self.connection_widget.setEnabled(False)
        # self.protocol_widget.setEnabled(False)

    @QtCore.pyqtSlot()
    def connect_to_laser(self):
        self.connect_button.setEnabled(False)
        self.disconnect_button.setEnabled(True)
        self.connected_text.setText("Status: connected")
        self.protocol_widget.setEnabled(True)
        self.status_widget.setEnabled(True)
        self.plugin.connect_laser()

    @QtCore.pyqtSlot()
    def disconnect_from_laser(self):
        self.plugin.disconnect_laser()
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.connected_text.setText("Status: disconnected")
        self.protocol_widget.setEnabled(False)
        self.status_widget.setEnabled(False)

    @QtCore.pyqtSlot()
    def laser_on(self):
        self.status_label.setText("ON")
        self.status_label.setFrameStyle(self.status_label.WinPanel | self.status_label.Raised)
        self.status_label.setStyleSheet('background-color: cyan')

    @QtCore.pyqtSlot()
    def laser_off(self):
        self.status_label.setText("OFF")
        self.status_label.setFrameStyle(self.status_label.WinPanel | self.status_label.Sunken)
        self.status_label.setStyleSheet(self.default_style)

    @QtCore.pyqtSlot()
    def protocol_running(self):
        self.laser_button.setEnabled(False)
        self.protocol_widget.setEnabled(False)

    @QtCore.pyqtSlot()
    def free_running(self):
        self.laser_button.setEnabled(True)
        self.protocol_widget.setEnabled(True)

    @QtCore.pyqtSlot()
    def create_protocol(self):
        dialog = StimulationDialog(self)
        result = dialog.exec_()
        if result:
            if dialog.params:
                self.plugin.create_stimulus(True, **dialog.params)
            else:
                self.plugin.create_stimulus(False)


class StimulationDialog(QtWidgets.QDialog):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        # Initialize params
        params = ('pre_stim_time', 'stim_time', 'inter_stimulus_interval', 'n_stims', 'post_stim_time')
        self.params = dict(zip(params, [0] * len(params)))
        if self.parent().plugin.stimulus is not None:
            for param in self.params.keys():
                self.params[param] = self.parent().plugin.stimulus.__getattribute__(param)

        # Create form layout
        self.setLayout(QtWidgets.QFormLayout())

        # Add row for each param
        self.value_editors = {}
        for param in self.params.keys():
            if param == 'n_stims':
                spinbox = QtWidgets.QSpinBox()
            else:
                spinbox = QtWidgets.QDoubleSpinBox()
            if self.params[param] is not None:
                spinbox.setValue(self.params[param])
            self.value_editors[param] = spinbox
            self.layout().addRow(QtWidgets.QLabel(param + ':'), spinbox)

        # Ok / cancel
        self.okbutton = QtWidgets.QPushButton('OK')
        self.okbutton.setFixedSize(100, 25)
        self.okbutton.clicked.connect(self.accept)
        self.cancelbutton = QtWidgets.QPushButton('Cancel')
        self.cancelbutton.setFixedSize(100, 25)
        self.cancelbutton.clicked.connect(self.reject)
        self.layout().addRow(self.okbutton, self.cancelbutton)

        self.setWindowTitle('Stimulation protocol')

    def accept(self) -> None:
        new_vals = dict()
        for param, editor in self.value_editors.items():
            new_vals[param] = editor.value()
        if all([new_vals['stim_time'], new_vals['n_stims']]):
            self.params.update(new_vals)
        else:
            self.params = None
        super().accept()
