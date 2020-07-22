from ..core.base import Worker, PydraProcess, pipe, WorkerConstructor
from threading import Timer, Event


class ProtocolProcess(PydraProcess):

    def __init__(self, *args):
        super().__init__(*args)

    @classmethod
    def create(cls, protocol, exit_flag, **kwargs):
        constructor = protocol.make(**kwargs)
        start_flag = Event()
        stop_flag = Event()
        finished_flag = Event()
        sender, receiver = pipe()
        process = cls(constructor, exit_flag, start_flag, stop_flag, finished_flag, receiver)
        return process, sender


class Protocol(Worker):

    def __init__(self):
        super().__init__()

    # @staticmethod
    # def make(cls, **kwargs):
    #     constructor = WorkerConstructor(cls, **kwargs)
    #     return constructor, kwargs


class StimulationProtocol(Protocol):

    def __init__(self, **kwargs):
        super().__init__()
        self.events = [(Event(), self.turn_stimulation_off,
                        Event(), self.turn_stimulation_on)]
        self.stimulus_df = None
        self.counter = 0
        self.timers = []

    # @classmethod
    # def make(cls, **kwargs):
    #     on_event = Event()
    #     off_event = Event()
    #     return super().make(cls, on_event=on_event, off_event=off_event)

    def turn_stimulation_off(self):
        self.events[0][0].clear()

    def turn_stimulation_on(self):
        self.events[1][0].clear()

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
        self.events[i][0].set()
        self.counter += 1
        if self.counter < len(self.timers):
            self.timers[self.counter].start()

    def cleanup(self):
        for timer in self.timers:
            timer.cancel()
        self.turn_stimulation_off()
        return
