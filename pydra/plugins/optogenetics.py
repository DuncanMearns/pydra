from ..process import Protocol
from .labjack import LabJack
from typing import Union
from PyQt5 import QtCore
from threading import Event, Timer


class Optogenetics(QtCore.QObject, LabJack):

    laserStateChanged = QtCore.pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.laser_state = 0

    @QtCore.pyqtSlot(int)
    def set_laser_state(self, state: int):
        """Send signal to labjack to turn laser on"""
        if state:
            self.laser_state = 1
            self.send_signal('DAC0', 3)
            print("LASER ON")
            self.laserStateChanged.emit(1)
        else:
            self.send_signal('DAC0', 0)
            self.laser_state = 0
            print("LASER OFF")
            self.laserStateChanged.emit(0)

        # self.laser_button.setText('LASER: ON')
        # self.laser_button.setStyleSheet('background-color: cyan')
        # self.u.writeRegister(self.DAC1_REGISTER, 1.5)  # in future can change laser power from here?
        # self.u.writeRegister(self.DAC1_REGISTER, 0)
        # self.laser_button.setText('LASER: OFF')
        # self.laser_button.setStyleSheet(self.laser_default_stylesheet)


class OptogeneticsProtocol(Protocol):

    def __init__(self, stimulus_df, **kwargs):
        super().__init__(**kwargs)
        self.stimulus_df = stimulus_df
        self.counter = 0
        self.events = [(Event(), self.turn_laser_off),
                       (Event(), self.turn_laser_on)]
        self.timers = []

    def timeout(self, i):
        self.events[i][0].set()
        self.counter += 1
        if self.counter < len(self.timers):
            self.timers[self.counter].start()

    def turn_laser_off(self):
        self.optogenetics.set_laser_state(0)
        self.events[0][0].clear()

    def turn_laser_on(self):
        self.optogenetics.set_laser_state(1)
        self.events[1][0].clear()

    def setup(self):
        self.optogenetics = Optogenetics()
        self.stimulus_df['stim'] = self.stimulus_df['stim'].apply(lambda x: 1 if x > 0 else 0)
        dt = self.stimulus_df['t'].diff()
        self.turn_laser_off()
        t0 = self.stimulus_df.loc[0]
        self.timers.append(Timer(t0.t, self.timeout, (t0.stim,)))
        if len(self.stimulus_df) > 1:
            for idx, stim in self.stimulus_df.loc[1:, 'stim'].iteritems():
                self.timers.append(Timer(dt.loc[idx], self.timeout, (stim,)))
        self.timers[0].start()

    def cleanup(self):
        for timer in self.timers:
            timer.cancel()
        self.turn_laser_off()
        return
