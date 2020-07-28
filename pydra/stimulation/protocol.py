from ..core import ProtocolWorker, ProtocolOutput
from threading import Timer
import time


class StimulationProtocol(ProtocolWorker):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events['stimulation_on'] = self.turn_stimulation_on
        self.events['stimulation_off'] = self.turn_stimulation_off
        self.stimulus_df = kwargs.get('stimulus_df', None)
        self.counter = 0
        self.timers = []

    def turn_stimulation_off(self):
        t = time.time()
        self.q.put(ProtocolOutput(t, 0))
        self.sender.put_nowait(ProtocolOutput(t, 0))

    def turn_stimulation_on(self):
        t = time.time()
        self.q.put(ProtocolOutput(t, 1))
        self.sender.put_nowait(ProtocolOutput(t, 1))

    def setup(self):
        self.counter = 0
        self.timers = []
        self.turn_stimulation_off()
        if self.stimulus_df is not None:
            self.stimulus_df['stimulation'] = self.stimulus_df['stimulation'].apply(lambda x: 1 if x > 0 else 0)
            dt = self.stimulus_df['t'].diff()
            t0 = self.stimulus_df.loc[0]
            self.timers.append(Timer(t0.t, self.timeout, (t0.stimulation,)))
            if len(self.stimulus_df) > 1:
                for idx, stim in self.stimulus_df.loc[1:, 'stimulation'].iteritems():
                    self.timers.append(Timer(dt.loc[idx], self.timeout, (stim,)))
            self.timers[0].start()

    def timeout(self, i):
        if i == 0:
            self.turn_stimulation_off()
        else:
            self.turn_stimulation_on()
        self.counter += 1
        if self.counter < len(self.timers):
            self.timers[self.counter].start()

    def cleanup(self):
        for timer in self.timers:
            timer.cancel()
        self.turn_stimulation_off()
        return
