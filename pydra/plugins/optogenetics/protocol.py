from ..utilities import LabJack
from ..protocols import StimulationProtocol


class OptogeneticsProtocol(StimulationProtocol, LabJack):

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
