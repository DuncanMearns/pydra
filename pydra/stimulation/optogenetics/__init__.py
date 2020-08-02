from ...core.plugin import Plugin
from ..utilities import LabJack
from ..protocol import StimulationProtocol
from ...gui.display import Plotter
from .widget import OptogeneticsWidget
from PyQt5 import QtCore
import pandas as pd


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

    def stimulation_off(self):
        self.set_laser_state(0)
        super().stimulation_off()

    def stimulation_on(self):
        self.set_laser_state(1)
        super().stimulation_on()


class OptogeneticsPlotter(Plotter):

    linked_plots = ["TailTracker"]

    def __init__(self, parent, name):
        super().__init__(parent, name)
        self.linked = False
        self.t0 = 0
        self.t = [0]
        self.laser = [0]
        self.laser_data = self.plot.plot([], [])

    def reset(self):
        for linked in self.linked_plots:
            if linked in [name for name in self.parent.plots.keys()]:
                self.plot.setXLink(self.parent.plots[linked])
                self.linked = True
                break
        self.t0 = 0
        self.t = [0]
        self.laser = [0]

    def update(self, *args, **kwargs):
        if not self.t0:
            self.t0 = args[0].timestamp
        if len(kwargs['protocol_data']):
            for (t, val) in kwargs['protocol_data']:
                self.t.extend([t - self.t0, t-self.t0])
                self.laser.extend([self.laser[-1], val])
            last_state = kwargs['protocol_data'][-1][1]
            if last_state:
                self.parent.parent().protocol.laserOn.emit()
            else:
                self.parent.parent().protocol.laserOff.emit()
        now = args[-1].timestamp
        t = self.t + [now - self.t0]
        laser = self.laser + [self.laser[-1]]
        self.laser_data.setData(t, laser)


class StimulusMaker:

    def __init__(self, pre_stim_time, stim_time, inter_stimulus_interval, n_stims, post_stim_time):
        self.pre_stim_time = pre_stim_time
        self.stim_time = stim_time
        self.inter_stimulus_interval = inter_stimulus_interval
        self.n_stims = n_stims
        self.post_stim_time = post_stim_time
        t, df = self.create()
        self.total_time = t
        self.stimulus_df = df

    def create(self):
        stimulus = []
        t = 0
        t += self.pre_stim_time
        stimulus.append((t, 1))
        for i in range(self.n_stims - 1):
            t += self.stim_time
            stimulus.append((t, 0))
            t += self.inter_stimulus_interval
            stimulus.append((t, 1))
        t += self.stim_time
        stimulus.append((t, 0))
        t += self.post_stim_time
        stimulus_df = pd.DataFrame(stimulus, columns=['t', 'stimulation'])
        return t, stimulus_df


class Optogenetics(Plugin):

    name = "Optogenetics"
    worker = OptogeneticsProtocol
    widget = OptogeneticsWidget
    plotter = OptogeneticsPlotter

    startEventLoop = QtCore.pyqtSignal()
    stopEventLoop = QtCore.pyqtSignal()
    protocolStarted = QtCore.pyqtSignal()
    protocolFinished = QtCore.pyqtSignal()
    laserOn = QtCore.pyqtSignal()
    laserOff = QtCore.pyqtSignal()

    def __init__(self, pydra, *args, **kwargs):
        super().__init__(pydra, *args, **kwargs)
        self.startEventLoop.connect(self.pydra.handler.start_protocol_event_loop)
        self.stopEventLoop.connect(self.pydra.handler.stop_protocol_event_loop)
        self.stimulus = None
        # Handle events from pydra
        self.pydra.started.connect(self.run_protocol)
        self.pydra.stopped.connect(self.end_protocol)
        # Laser state
        self.laser_state = 0
        self.laserOn.connect(self.set_laser_state_on)
        self.laserOff.connect(self.set_laser_state_off)

    def connect_laser(self):
        self.startEventLoop.emit()

    def disconnect_laser(self):
        self.stopEventLoop.emit()

    def laser_on(self):
        self.pydra.handler.send_event(self.name, 'stimulation_on', ())
        self.laserOn.emit()

    def laser_off(self):
        self.pydra.handler.send_event(self.name, 'stimulation_off', ())
        self.laserOff.emit()

    def set_laser_state_on(self):
        self.laser_state = 1

    def set_laser_state_off(self):
        self.laser_state = 0

    def toggle_laser(self):
        if self.laser_state:
            self.laser_off()
        else:
            self.laser_on()

    def create_stimulus(self, set_active: bool, **kwargs):
        if set_active:
            self.stimulus = StimulusMaker(**kwargs)
            df = self.stimulus.stimulus_df
            self.pydra.handler.send_event(self.name, 'set_param', ('stimulus_df', df))
            self.pydra.recordTime = self.stimulus.total_time
        else:
            self.stimulus = None
            self.pydra.handler.send_event(self.name, 'set_param', ('stimulus_df', None))
            self.pydra.recordTime = 0

    def run_protocol(self):
        if (self.pydra.currentState == self.pydra.states['record']) and self.stimulus:
            self.protocolStarted.emit()
            self.pydra.handler.send_event(self.name, 'run_protocol', ())

    def end_protocol(self):
        if self.stimulus:
            self.pydra.handler.send_event(self.name, 'end_protocol', ())
            self.protocolFinished.emit()
