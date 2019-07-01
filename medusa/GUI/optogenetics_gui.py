from .camera_gui import CameraGUI
from ..helpers.trackers import Optogenetics
from ..helpers.GUI_helpers.lines import HorizontalLine
from PyQt5 import QtWidgets
import u3


class OptogeneticsGUI(CameraGUI):

    DAC0_REGISTER = 5000
    DAC1_REGISTER = 5002

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ===========
        # SETUP LASER
        # ===========
        print('Connecting to labjack...', end=' ')
        self.u = u3.U3()
        self.u.writeRegister(self.DAC0_REGISTER, 0)
        self.u.writeRegister(self.DAC1_REGISTER, 0)
        self.laser_on = False
        print('done!\n')
        # ===========
        # ADD TRACKER
        # ===========
        self.trackers.append(Optogenetics(self, self.buffer_tracking, self.buffer_display))
        self.gui_constructor_methods.append(self.add_laser_button)

    def add_laser_button(self, **kwargs):
        """

        Parameters
        ----------
        row : int
            row number passed to GraphicsLayoutWidget
        col : int
            column number passed to GraphicsLayoutWidget
        """
        if not 'layout_features' in dir(self):
            self._add_features_dock()
        layout_laser_control = QtWidgets.QVBoxLayout()
        layout_laser_control.addWidget(QtWidgets.QLabel('Laser control'))
        self.laser_button = QtWidgets.QPushButton('LASER: OFF')
        self.laser_button.setFixedSize(self.button_width, self.button_height)
        self.laser_button.clicked.connect(self.toggle_laser)
        self.laser_default_stylesheet = self.laser_button.styleSheet()
        layout_laser_control.addWidget(self.laser_button)
        self.layout_features.addLayout(layout_laser_control)
        self.layout_features.addWidget(HorizontalLine())

    def turn_laser_on(self):
        """Send signal to labjack to turn laser on"""
        self.laser_button.setText('LASER: ON')
        self.laser_button.setStyleSheet('background-color: cyan')
        self.laser_on = True
        self.u.writeRegister(self.DAC0_REGISTER, 5)
        self.u.writeRegister(self.DAC1_REGISTER, 1.5)  # in future can change laser power from here?

    def turn_laser_off(self):
        """Send signal to labjack to turn laser off"""
        self.u.writeRegister(self.DAC0_REGISTER, 0)
        self.u.writeRegister(self.DAC1_REGISTER, 0)
        self.laser_button.setText('LASER: OFF')
        self.laser_button.setStyleSheet(self.laser_default_stylesheet)
        self.laser_on = False

    def toggle_laser(self):
        """Toggle laser on or off"""
        if not self.laser_on:
            self.turn_laser_on()
        else:
            self.turn_laser_off()
