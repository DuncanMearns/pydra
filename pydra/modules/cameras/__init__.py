from .widget import CameraWidget
from .ximea import XimeaCamera
from .pike import PikeCamera


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
