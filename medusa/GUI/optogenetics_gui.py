from .camera_gui import CameraGUI
from ..helpers.trackers import Optogenetics
from ..helpers.GUI_helpers.lines import HorizontalLine
from ..helpers.GUI_helpers import CollapsibleWidget
from PyQt5 import QtWidgets, QtGui, QtCore
import u3


class Protocol(QtCore.QObject):

    def __init__(self, parent):
        super().__init__(parent)

    def start(self):
        return


class StimulationProtocol(Protocol):

    def __init__(self, parent, prestim, stimtime, nstim, isi):
        super().__init__(parent)
        self.prestim = prestim
        self.stimtime = stimtime
        self.nstim = nstim
        self.isi = isi
        self._initialise_timers()

    def _initialise_timers(self):

        self.prestim_timer = QtCore.QTimer()
        self.prestim_timer.setSingleShot(True)
        self.prestim_timer.setInterval(self.prestim * 1000)
        self.prestim_timer.timeout.connect(self.start_stimulation)

        self.stimtime_timer = QtCore.QTimer()
        self.stimtime_timer.setSingleShot(True)
        self.stimtime_timer.setInterval(self.stimtime * 1000)
        self.stimtime_timer.timeout.connect(self.stop_stimulation)

        self.isi_timer = QtCore.QTimer()
        self.isi_timer.setSingleShot(True)
        self.isi_timer.setInterval(self.isi * 1000)
        self.isi_timer.timeout.connect(self.start_stimulation)

        self.counter = 0

    def start_stimulation(self):
        if self.counter == self.nstim:
            self.parent().stop_recording()
        else:
            self.parent().turn_laser_on()
            self.stimtime_timer.start()
            self.counter += 1

    def stop_stimulation(self):
        self.parent().turn_laser_off()
        self.isi_timer.start()

    def start(self):
        self._initialise_timers()
        self.prestim_timer.start()
        return

    @classmethod
    def make(cls, parent):
        if parent.protocol is not None:
            dialog = CreateStimulationProtocol(parent,
                                               prestim=parent.protocol.prestim,
                                               stimtime=parent.protocol.stimtime,
                                               nstim=parent.protocol.nstim,
                                               isi=parent.protocol.isi)
        else:
            dialog = CreateStimulationProtocol(parent)
        result = dialog.exec_()
        result = (result == QtWidgets.QDialog.Accepted)
        if result:
            prestim = dialog.prestim_le.text()
            stimtime = dialog.stimtime_le.text()
            nstim = dialog.nstim_le.text()
            isi = dialog.isi_le.text()
            if any([len(prestim) == 0, len(stimtime) == 0, len(nstim) == 0, len(isi) == 0]):
                protocol = None
            else:
                protocol = cls(parent,
                               prestim=float(str(prestim)),
                               stimtime=float(str(stimtime)),
                               nstim=int(str(nstim)),
                               isi=float(str(isi)))
        else:
            protocol = None
        return result, protocol


class CreateStimulationProtocol(QtWidgets.QDialog):

    def __init__(self, parent, **kwargs):
        super().__init__(parent)

        layout = QtWidgets.QFormLayout()
        num_validator = QtGui.QDoubleValidator()
        int_validator = QtGui.QIntValidator()
        self.prestim_le = QtWidgets.QLineEdit()
        self.prestim_le.setValidator(num_validator)
        self.prestim_le.setPlaceholderText(str(kwargs.get('prestim', '')))
        layout.addRow(QtWidgets.QLabel('Pre-stimulation time (s):'), self.prestim_le)

        self.stimtime_le = QtWidgets.QLineEdit()
        self.stimtime_le.setValidator(num_validator)
        self.stimtime_le.setPlaceholderText(str(kwargs.get('stimtime', '')))
        layout.addRow(QtWidgets.QLabel('Stimulation time (s):'), self.stimtime_le)

        self.nstim_le = QtWidgets.QLineEdit()
        self.nstim_le.setValidator(int_validator)
        self.nstim_le.setPlaceholderText(str(kwargs.get('nstim', '')))
        layout.addRow(QtWidgets.QLabel('Number of stimulations:'), self.nstim_le)

        self.isi_le = QtWidgets.QLineEdit()
        self.isi_le.setValidator(num_validator)
        self.isi_le.setPlaceholderText(str(kwargs.get('isi', '')))
        layout.addRow(QtWidgets.QLabel('Inter-stimulus interval (s):'), self.isi_le)

        # Ok / cancel
        self.okbutton = QtWidgets.QPushButton('OK')
        self.okbutton.setFixedSize(100, 25)
        self.okbutton.clicked.connect(self.accept)
        self.cancelbutton = QtWidgets.QPushButton('Cancel')
        self.cancelbutton.setFixedSize(100, 25)
        self.cancelbutton.clicked.connect(self.reject)
        layout.addRow(self.okbutton, self.cancelbutton)

        self.setLayout(layout)
        self.setWindowTitle('Stimulation protocol')


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

    def add_laser_button(self):
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
        # Add stimulation options
        self.laser_options = CollapsibleWidget('Options')
        layout_laser_control.addWidget(self.laser_options)
        layout_laser_options = QtWidgets.QVBoxLayout()
        self.stimulation_protocol_button = QtWidgets.QPushButton('Stim. protocol')
        self.stimulation_protocol_button.clicked.connect(self.create_stimulation_protocol)
        layout_laser_options.addWidget(self.stimulation_protocol_button)
        self.laser_options.setContentLayout(layout_laser_options)

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

    def create_stimulation_protocol(self):
        ret, protocol = StimulationProtocol.make(self)
        self.protocol = protocol
