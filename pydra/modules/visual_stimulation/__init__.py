from .worker import VisualStimulationWorker
from .widget import VisualStimulationWidget
from .screengrabber import ScreenGrabber
from .stimulus import Stimulus, Wait

from ...base import CSVSaver
from ...configuration import PydraModule
from .widget import *
import os


class VisualStimulationSaver(CSVSaver):

    name = "visual_stimulation_saver"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_callbacks["run"] = self.dummy

    @staticmethod
    def new_file(directory, filename, ext=""):
        if ext:
            filename = ".".join((filename + "_stimulus", ext))
        f = os.path.join(directory, filename)
        return f

    def dummy(self, *args, **kwargs):
        """This needs to be here to prevent pydra event messages calling the run method accidentally because Duncan sucks at programming :("""
        return


class VisualStimulationModule(PydraModule):

    def __init__(self, window_params=None, **kwargs):
        if window_params:
            VisualStimulationWorker.window_params = window_params
        super().__init__(VisualStimulationWorker, (), worker_kwargs=kwargs, saver=VisualStimulationSaver, widget=VisualStimulationWidget)
