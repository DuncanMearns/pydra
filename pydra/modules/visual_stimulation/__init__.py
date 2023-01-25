from .worker import VisualStimulationWorker
from .widget import VisualStimulationWidget
from .screengrabber import ScreenGrabber
from .stimulus import Stimulus, Wait


PSYCHOPY = {
    "worker": VisualStimulationWorker,
    "controller": VisualStimulationWidget,
    "plotter": ScreenGrabber,
    "params": {}
}
