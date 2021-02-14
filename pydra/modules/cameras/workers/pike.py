try:
    from pymba import Vimba
    from pymba.vimbaexception import VimbaException
except ImportError:
    pass
from pydra.modules.cameras.workers._base import CameraAcquisition


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

    def setup(self):
        self.vimba = Vimba()
        self.vimba.startup()

        camera_ids = self.vimba.camera_ids()
        self.camera = self.vimba.camera(camera_ids[self.id])

        # Start camera
        self.camera.open()
        self.set_params(
            frame_rate=self.frame_rate,
            frame_size=self.frame_size,
            exposure=self.exposure,
            gain=self.gain
        )
        self.frame = self.camera.new_frame()
        self.frame.announce()

        self.camera.start_capture()
        self.frame.queue_for_capture()
        self.camera.run_feature_command("AcquisitionStart")

    def read(self):
        try:
            self.frame.wait_for_capture(self.timeout_ms)
            self.frame.queue_for_capture()
            frame = self.frame.buffer_data_numpy()
        except VimbaException:
            frame = self.empty()
        return frame

    def set_frame_rate(self, fps: float) -> bool:
        try:
            self.camera.AcquisitionFrameRate = fps
            return super().set_frame_rate(fps)
        except VimbaException:
            return False

    def set_frame_size(self, width: int, height: int) -> bool:
        try:
            self.camera.Width = width
            self.camera.Height = height
            return super().set_frame_size(width, height)
        except VimbaException:
            return False

    def set_offsets(self, x, y) -> bool:
        return False

    def set_exposure(self, msec: int) -> bool:
        try:
            self.camera.ExposureTime = msec
            super().set_exposure(msec)
        except VimbaException:
            return False

    def set_gain(self, gain: float) -> bool:
        try:
            self.camera.Gain = gain
            return super().set_gain(gain)
        except VimbaException:
            return False

    def cleanup(self):
        self.frame.wait_for_capture(self.timeout_ms)
        self.camera.run_feature_command("AcquisitionStop")
        self.camera.end_capture()
        self.camera.revoke_all_frames()
        self.vimba.shutdown()
