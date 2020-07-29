from .base import Stimulus
from psychopy import visual, core


class GratingsStimulus(Stimulus):

    clock = core.MonotonicClock()

    def __init__(self, spatial, temporal, duration, **kwargs):
        super().__init__(**kwargs)
        self.tf = temporal
        self.grating = visual.GratingStim(win=self.window, pos=(0, 0), size=self.window.size, sf=spatial, color='black', colorSpace=u'rgb')
        self.duration = duration
        self.time = self.clock.getTime()

    def update(self):
        if self.clock.getTime() - self.time < self.duration:
            self.grating.phase = (self.grating.phase[0] + (self.tf / 360), self.grating.phase[1])
            self.grating.draw()
        else:
            self.finished = True
