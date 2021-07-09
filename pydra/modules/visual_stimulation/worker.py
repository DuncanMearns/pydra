from pydra.core import Acquisition
from psychopy import visual
import importlib.util


class VisualStimulationWorker(Acquisition):

    name = "visual_stimulation"
    window_params = {}

    def __init__(self, stimulus_file=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stimulus_file = stimulus_file
        self.stimulus_list = []
        self.events["load"] = self.load_protocol
        self.events["run"] = self.run_protocol
        self.events["interrupt"] = self.interrupt_protocol
        self.window = None  # specified at setup

    def setup(self):
        self.window = visual.Window(**self.window_params)
        if self.stimulus_file:
            self.load_protocol()

    def acquire(self):
        pass

    def cleanup(self):
        self.window.close()

    def load_protocol(self, **kwargs):
        try:
            spec = importlib.util.spec_from_file_location("stimulus", self.stimulus_file)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        except AttributeError:
            print("Path to stimulus not specified.")
            return
        except FileNotFoundError:
            print("Path to stimulus file does not exist.")
            return
        try:
            stimulus_list = mod.stimulus_list
            self.stimulus_list = list(stimulus_list)
        except AttributeError:
            print(f"{self.stimulus_file} does not contain a `stimulus_list`.")
        except TypeError:
            print("`stimulus_list` must be a list of Stimulus objects")
        # Set the window for each stimulus object
        for stimulus in self.stimulus_list:
            stimulus.window = self.window
        print(f"Stimulus loaded from: {self.stimulus_file}")

    def run_protocol(self, **kwargs):
        print(self.logging_info())
        # self.stimulus.start()

    def interrupt_protocol(self, **kwargs):
        # self.stimulus.stop()
        pass

    def logging_info(self):
        info = {}
        for stimulus in self.stimulus_list:
            for key, val in stimulus.__dict__.items():
                if not key.startswith("_"):
                    info[key] = val
        return info
