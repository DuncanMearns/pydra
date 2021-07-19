from .video import VideoWorker
from ..widget import CameraWidget, FramePlotter

VIDEO = {
    "worker": VideoWorker,
    "params": {},
    "controller": CameraWidget,
    "plotter": FramePlotter
}
