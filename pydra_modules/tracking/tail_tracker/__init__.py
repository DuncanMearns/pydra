from .worker import TailTrackingWorker
from .widget import TailTrackerWidget, TailPlotter, TailOverlay


TAIL_TRACKER = {
    "worker": TailTrackingWorker,
    "params": {},
    "controller": TailTrackerWidget,
    "plotter": TailPlotter
}
