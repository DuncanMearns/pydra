from .ximea import XimeaCamera
from ..widget import CameraWidget, FramePlotter

XIMEA = {
    "worker": XimeaCamera,
    "params": {},
    "controller": CameraWidget,
    "plotter": FramePlotter
}
