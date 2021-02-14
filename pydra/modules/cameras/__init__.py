from .widget import CameraWidget
from .workers import *


__all__ = ["PIKE", "XIMEA"]


PIKE = {
    "worker": PikeCamera,
    "params": {},
    "widget": CameraWidget,
}


XIMEA = {
    "worker": XimeaCamera,
    "params": {},
    "widget": CameraWidget,
}
