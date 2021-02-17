try:
    from pymba import Vimba
    from pymba import VimbaException
except ImportError:
    pass
from pydra.modules.cameras.workers._base import CameraAcquisition
import numpy as np


class PikeCamera(CameraAcquisition):
    """Class for controlling an AVT camera.
    Uses the Vimba interface pymba
    (module documentation `here <https://github.com/morefigs/pymba>`_).
    """

    name = "pike"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = 0
        self.timeout_ms = 1000  # Set timeout for frame acquisition. Give this as input?
        self.frame = None
        # Start vimba
        self._vimba = Vimba()
        self._vimba.startup()

    def start_acquisition(self):
        self.frame = self.camera.new_frame()
        self.frame.announce()
        self.frame.queue_for_capture()
        self.camera.start_capture()
        self.camera.run_feature_command("AcquisitionStart")

    def stop_acquisition(self):
        self.camera.run_feature_command("AcquisitionStop")
        self.camera.end_capture()
        self.camera.flush_capture_queue()
        self.camera.revoke_all_frames()

    def setup(self):
        # Open camera
        camera_ids = self._vimba.camera_ids()
        self.camera = self._vimba.camera(camera_ids[self.id])
        self.camera.open()

        # Start camera
        self.start_acquisition()
        self.set_params(
            frame_size=self.frame_size,
            exposure=self.exposure,
            gain=self.gain
        )

    def read(self):
        try:
            self.frame.wait_for_capture(self.timeout_ms)
            self.frame.queue_for_capture()
            frame = self.frame.buffer_data_numpy()
        except VimbaException:
            frame = np.zeros(self.frame_size[::-1], dtype="uint8")
        return frame

    def set_frame_rate(self, fps: float) -> bool:
        try:
            self.camera.AcquisitionFrameRate = fps
            return super().set_frame_rate(fps)
        except VimbaException:
            return False

    def set_frame_size(self, width: int, height: int) -> bool:
        self.stop_acquisition()
        width = width - (width % 4)
        height = height - (height % 2)
        try:
            self.camera.Width = width
            self.camera.Height = height
            ret = super().set_frame_size(width, height)
        except VimbaException:
            ret = False
        self.start_acquisition()
        return ret

    def set_offsets(self, x, y) -> bool:
        return False

    def set_exposure(self, u: int) -> bool:
        try:
            self.camera.ExposureTime = u
            return super().set_exposure(u)
        except VimbaException:
            return False

    def set_gain(self, gain: float) -> bool:
        try:
            self.camera.Gain = gain
            return super().set_gain(gain)
        except VimbaException:
            return False

    def cleanup(self):
        print("stopping acquisition")
        self.stop_acquisition()
        print("closing camera")
        self.camera.close()
        print("shutting down vimba")
        self._vimba.shutdown()
