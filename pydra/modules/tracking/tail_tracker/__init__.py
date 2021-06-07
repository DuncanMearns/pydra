from .worker import TailTrackingWorker
from .widget import TailTrackerWidget


TAIL_TRACKER = {
    "worker": TailTrackingWorker,
    "params": {},
    "widget": TailTrackerWidget,
}
