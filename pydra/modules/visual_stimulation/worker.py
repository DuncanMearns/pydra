from pydra import Acquisition
from .stimulus import ProtocolRunner, Stimulus, Wait
from psychopy import visual
import time


class VisualStimulationWorker(Acquisition):

    name = "visual_stimulation"
    window_params = {}
    gui_events = ("run", "interrupt")

    def __init__(self, stimulus_file=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stimulus_file = stimulus_file
        self.protocol_runner = None
        self.event_callbacks["load"] = self.load_protocol
        self.event_callbacks["run"] = self.run_protocol
        self.event_callbacks["interrupt"] = self.interrupt_protocol
        self.window = None  # specified at setup

    def setup(self):
        self.window = visual.Window(**self.window_params)
        # ProtocolRunner.window = self.window
        if self.stimulus_file:
            self.protocol_runner = ProtocolRunner.from_protocol(self.window, self.stimulus_file)
        else:
            self.protocol_runner = ProtocolRunner(self.window)

    def acquire(self):
        is_running = self.protocol_runner()
        if is_running:
            if self.protocol_runner.current_stimulus:
                logging_info = self.protocol_runner.logging_info()
                t = time.time()
                self.send_timestamped(t, logging_info)

    def cleanup(self):
        self.window.close()

    def load_protocol(self, **kwargs):
        if "stimulus_file" in kwargs:
            self.stimulus_file = kwargs["stimulus_file"]
            print(f"Loading stimulus file: {self.stimulus_file}")
        self.protocol_runner = ProtocolRunner.from_protocol(self.window, self.stimulus_file)

    def run_protocol(self, **kwargs):
        self.protocol_runner.start()

    def interrupt_protocol(self, **kwargs):
        self.protocol_runner.stop()
