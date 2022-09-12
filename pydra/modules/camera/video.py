from .camera import CameraAcquisition, setter
from .widget import CameraWidget, FramePlotter
import cv2


__all__ = ("VideoAcquisition", "VIDEO")


class VideoAcquisition(CameraAcquisition):

    name = "video"

    def __init__(self, filepath, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filepath = str(filepath)

    @property
    def t(self):
        return self._t

    # @property
    # def frame_rate(self):
    #     return self._frame_rate

    @setter
    def frame_rate(self, val):
        self._frame_rate = val
        self._t = max(1, int(1000 / val))

    def setup(self):
        self.cap = cv2.VideoCapture(self.filepath)

    def read(self):
        if self.cap.get(cv2.CAP_PROP_POS_FRAMES) >= self.frame_count:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.reset_frame_number()
        ret, frame = self.cap.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.waitKey(self.t)
        return frame

    @property
    def frame_count(self):
        return self.cap.get(cv2.CAP_PROP_FRAME_COUNT)


VIDEO = {
    "worker": VideoAcquisition,
    "params": {},
    "controller": CameraWidget,
    "plotter": FramePlotter
}
