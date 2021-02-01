try:
    from pymba import Vimba
    from pymba.vimbaexception import VimbaException
except ImportError:
    pass
from ..worker import CameraAcquisition


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

        # Set params
        self.camera.Width = self.width
        self.camera.Height = self.height
        self.camera.AcquisitionFrameRate = self.frame_rate
        self.camera.ExposureTime = self.exposure
        self.camera.Gain = self.gain

        self.frame = self.cam.new_frame()
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

    def cleanup(self):
        self.frame.wait_for_capture(self.timeout_ms)
        self.camera.run_feature_command("AcquisitionStop")
        self.camera.end_capture()
        self.camera.revoke_all_frames()
        self.vimba.shutdown()
