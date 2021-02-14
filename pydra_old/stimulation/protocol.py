from ..core import ProtocolWorker, ProtocolOutput
from threading import Timer
import time


class StimulationProtocol(ProtocolWorker):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events['stimulation_on'] = self.stimulation_on
        self.events['stimulation_off'] = self.stimulation_off
        self.events['run_protocol'] = self.run_protocol
        self.events['end_protocol'] = self.cleanup
        self.stimulus_df = kwargs.get('stimulus_df', None)
        self.counter = 0
        self.timers = []

    def stimulation_off(self):
        t = time.time()
        self.q.put(ProtocolOutput(t, 0))
        self.sender.put_nowait(ProtocolOutput(t, 0))

    def stimulation_on(self):
        t = time.time()
        self.q.put(ProtocolOutput(t, 1))
        self.sender.put_nowait(ProtocolOutput(t, 1))

    def run_protocol(self):
        self.counter = 0
        self.timers = []
        self.stimulation_off()
        if self.stimulus_df is not None:
            self.stimulus_df['stimulation'] = self.stimulus_df['stimulation'].apply(lambda x: 1 if x > 0 else 0)
            dt = self.stimulus_df['t'].diff()
            t0 = self.stimulus_df.loc[0]
            self.timers.append(Timer(t0.t, self.timeout, (t0.stimulation,)))
            if len(self.stimulus_df) > 1:
                for idx, stim in self.stimulus_df.loc[1:, 'stimulation'].iteritems():
                    self.timers.append(Timer(dt.loc[idx], self.timeout, (stim,)))
            self.timers[0].start()

    def setup(self):
        self.stimulation_off()

    def timeout(self, i):
        if i == 0:
            self.stimulation_off()
        else:
            self.stimulation_on()
        self.counter += 1
        if self.counter < len(self.timers):
            self.timers[self.counter].run()

    def cleanup(self):
        for timer in self.timers:
            timer.cancel()
        self.stimulation_off()
        return
