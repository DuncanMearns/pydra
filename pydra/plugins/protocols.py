from ..core import Worker
from threading import Timer, Event
import time


class Protocol(Worker):

    def __init__(self, messages=None, output=None):
        super().__init__()
        self.messages = messages
        self.output = output

    def _handle_events(self):
        event_name = self.messages.recv()
        if event_name:
            self.events[event_name][0].set()
        super()._handle_events()


class StimulationProtocol(Protocol):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events['stimulation_on'] = (Event(), self.turn_stimulation_on)
        self.events['stimulation_off'] = (Event(), self.turn_stimulation_off)
        self.stimulus_df = None
        self.counter = 0
        self.timers = []

    def turn_stimulation_off(self):
        self.events['stimulation_off'][0].clear()
        t = time.clock()
        self.output.send((t, 'stimulation_off'))

    def turn_stimulation_on(self):
        self.events['stimulation_on'][0].clear()
        t = time.clock()
        self.output.send((t, 'stimulation_on'))

    def setup(self):
        self.counter = 0
        self.timers = []
        self.turn_stimulation_off()
        if self.stimulus_df is not None:
            self.stimulus_df['stimulation'] = self.stimulus_df['stimulation'].apply(lambda x: 1 if x > 0 else 0)
            dt = self.stimulus_df['t'].diff()
            t0 = self.stimulus_df.loc[0]
            self.timers.append(Timer(t0.t, self.timeout, (t0.stim,)))
            if len(self.stimulus_df) > 1:
                for idx, stim in self.stimulus_df.loc[1:, 'stimulation'].iteritems():
                    self.timers.append(Timer(dt.loc[idx], self.timeout, (stim,)))
            self.timers[0].start()

    def timeout(self, i):
        if i == 0:
            self.events['stimulation_off'][0].set()
        else:
            self.events['stimulation_on'][0].set()
        self.counter += 1
        if self.counter < len(self.timers):
            self.timers[self.counter].start()

    def cleanup(self):
        for timer in self.timers:
            timer.cancel()
        self.turn_stimulation_off()
        return
