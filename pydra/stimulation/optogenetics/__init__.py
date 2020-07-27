from ...core.plugin import Plugin
from ..utilities import LabJack
from ..protocol import StimulationProtocol
from .widget import OptogeneticsWidget
from PyQt5 import QtCore


class OptogeneticsProtocol(LabJack, StimulationProtocol):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.laser_state = 0

    def set_laser_state(self, state):
        """Send signal to labjack to turn laser on"""
        if state:
            self.laser_state = 1
            self.send_signal('DAC0', 3)
            print("LASER ON")
        else:
            self.send_signal('DAC0', 0)
            self.laser_state = 0
            print("LASER OFF")
        # self.laser_button.setText('LASER: ON')
        # self.laser_button.setStyleSheet('background-color: cyan')
        # self.u.writeRegister(self.DAC1_REGISTER, 1.5)  # in future can change laser power from here?
        # self.u.writeRegister(self.DAC1_REGISTER, 0)
        # self.laser_button.setText('LASER: OFF')
        # self.laser_button.setStyleSheet(self.laser_default_stylesheet)

    def turn_stimulation_off(self):
        self.set_laser_state(0)
        super().turn_stimulation_off()

    def turn_stimulation_on(self):
        self.set_laser_state(1)
        super().turn_stimulation_on()


class Optogenetics(Plugin):

    name = "Optogenetics"
    worker = OptogeneticsProtocol
    widget = OptogeneticsWidget

    startProtocol = QtCore.pyqtSignal()
    stopProtocol = QtCore.pyqtSignal()
    laserEvent = QtCore.pyqtSignal(str, str, tuple)

    def __init__(self, pydra, *args, **kwargs):
        super().__init__(pydra, *args, **kwargs)
        self.startProtocol.connect(self.pydra.handler.start_protocol_event_loop)
        self.stopProtocol.connect(self.pydra.handler.stop_protocol_event_loop)
        self.laserEvent.connect(self.pydra.handler.send_event)

    def connect_laser(self):
        self.startProtocol.emit()

    def disconnect_laser(self):
        self.stopProtocol.emit()

    def set_laser(self, val):
        if val:
            self.laserEvent.emit(self.name, 'stimulation_on', ())
        else:
            self.laserEvent.emit(self.name, 'stimulation_off', ())
