from pydra.core import Acquisition
from psychopy import visual
from .stimulus import Stimulus


class VisualStimulationWorker(Acquisition):

    name = "visual_stimulation"
    window_params = {}

    def __init__(self, stimulus=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stimulus_class = stimulus or Stimulus
        self.events["run_stimulus"] = self.run_stimulus
        self.events["interrupt"] = self.interrupt_stimulus
        self.window = None
        self.stimulus = None

    def setup(self):
        self.window = visual.Window(**self.window_params)
        self.stimulus = self.stimulus_class(self.window)

    def acquire(self):
        if self.stimulus.is_running():
            self.stimulus.update()

    def cleanup(self):
        self.window.close()

    def run_stimulus(self, **kwargs):
        print(self.logging_info())
        self.stimulus.start()
        self.stimulus.set_running(True)

    def interrupt_stimulus(self, **kwargs):
        self.stimulus.stop()
        self.stimulus.set_running(False)

    def logging_info(self):
        info = {}
        for key, val in self.stimulus.__dict__.items():
            if not key.startswith("_"):
                info[key] = val
        return info
