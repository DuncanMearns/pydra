from pydra import PydraModule, Worker, CSVSaver
from pydra.gui import ControlWidget
from pydra.gui.helpers import TimeUnitWidget

from PyQt5 import QtWidgets, QtCore
import numpy as np
import sounddevice as sd
import time


class SpeakerWorker(Worker):

    name = "speaker"
    gui_events = ("play_sound",)

    def __init__(self, frequency=1000, samplerate=44100, duration=0.1, delay=0.1, amplitude=1., *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frequency = frequency
        self.samplerate = samplerate
        self.duration = int(duration * 1000)
        self.delay = int(delay * 1000)
        self.amplitude = amplitude

    @property
    def duration(self):
        return self._duration_ms / 1000.

    @duration.setter
    def duration(self, ms):
        self._duration_ms = ms

    @property
    def delay(self):
        return self._delay_ms / 1000.

    @delay.setter
    def delay(self, ms):
        self._delay_ms = ms

    @property
    def pulse_array(self) -> np.ndarray:
        pre_pulse = np.zeros((int(self.delay * self.samplerate), 2))
        pulse = self.sine(self.frequency, self.duration, self.samplerate, self.amplitude)
        pulse = np.array([pulse, pulse]).T
        return np.concatenate([pre_pulse, pulse, pre_pulse], axis=0)

    @property
    def params(self) -> dict:
        return dict(frequency=self.frequency,
                    duration=self.duration,
                    delay=self.delay,
                    amplitude=self.amplitude)

    def play_sound(self, **kwargs):
        sound = self.pulse_array
        t = time.time()
        sd.play(sound)
        self.send_timestamped(t, self.params)

    def stop_sound(self, **kwargs):
        sd.stop()

    def set_params(self, **kwargs):
        target = kwargs.get("target", self.name)
        if target == self.name:
            params = kwargs.get("params", {})
            for param, val in params.items():
                try:
                    setattr(self, param, val)
                    self.send_timestamped(time.time(), self.params)
                except AttributeError:
                    pass

    @staticmethod
    def sine(frequency, length, rate, amplitude=1.):
        length = int(length * rate)
        factor = float(frequency) * (np.pi * 2) / rate
        return np.sin(np.arange(length) * factor) * amplitude


class SpeakerWidget(ControlWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLayout(QtWidgets.QFormLayout())
        # Frequency widget
        self.frequency_widget = QtWidgets.QSpinBox()
        self.frequency_widget.setMinimum(100)
        self.frequency_widget.setMaximum(20_000)
        self.frequency_widget.setValue(self.params.get("frequency", 1000))
        self.frequency_widget.setSuffix(" Hz")
        self.frequency_widget.valueChanged.connect(self.value_changed)
        self.layout().addRow("Frequency", self.frequency_widget)
        # Duration widget
        self.duration_widget = TimeUnitWidget()
        self.duration_widget.addMilliseconds(minval=1, maxval=1000)
        self.duration_widget.addSeconds(minval=1, maxval=5)
        self.duration_widget.setValue(int(1000 * self.params.get("duration", 100)))
        self.duration_widget.valueChanged.connect(self.value_changed)
        self.layout().addRow("Duration", self.duration_widget)
        # Delay widget
        self.delay_widget = TimeUnitWidget()
        self.delay_widget.addMilliseconds(minval=10, maxval=1000)
        self.delay_widget.addSeconds(minval=1, maxval=5)
        self.delay_widget.setValue(int(1000 * self.params.get("delay", 100)))
        self.delay_widget.valueChanged.connect(self.value_changed)
        self.layout().addRow("Delay", self.delay_widget)
        # Samplerate widget
        self.samplerate_widget = QtWidgets.QComboBox()
        self._samplerates = (44100, 48000)
        for rate in self._samplerates:
            self.samplerate_widget.addItem(str(rate))
        self.samplerate_widget.currentIndexChanged.connect(self.value_changed)
        self.layout().addRow("Sample rate", self.samplerate_widget)
        # Button
        self.button = QtWidgets.QPushButton("PLAY")
        self.button.clicked.connect(self.play_sound)
        self.layout().addRow("Sound", self.button)

    @QtCore.pyqtSlot(int)
    def value_changed(self, val):
        freq = self.frequency_widget.value()
        duration = self.duration_widget.value
        delay = self.delay_widget.value
        idx = self.samplerate_widget.currentIndex()
        rate = self._samplerates[idx]
        self.send_event("set_params", params=dict(frequency=freq, duration=duration, delay=delay, samplerate=rate))

    @QtCore.pyqtSlot()
    def play_sound(self):
        self.send_event("play_sound")


class SpeakerSaver(CSVSaver):
    name = "speaker_saver"


SPEAKER = PydraModule(SpeakerWorker,
                      worker_kwargs={
                          "frequency": 1000,
                          "samplerate": 44100,
                          "duration": 0.006,
                          "delay": 0.1},
                      saver=SpeakerSaver,
                      widget=SpeakerWidget)
