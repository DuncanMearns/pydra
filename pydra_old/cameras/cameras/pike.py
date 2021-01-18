try:
    from pymba import Vimba
    from pymba.vimbaexception import VimbaException
except ImportError:
    pass
from .camera_worker import CameraAcquisitionWorker


class PikeCamera(CameraAcquisitionWorker):
    """Class for controlling an AVT camera.
    Uses the Vimba interface pymba
    (module documentation `here <https://github.com/morefigs/pymba>`_).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timeout_ms = 1000  # Set timeout for frame acquisition. Give this as input?
        self.frame = None

    def open(self):
        """ """
        self.vimba = Vimba()
        self.vimba.startup()

        camera_ids = self.vimba.camera_ids()
        self.cam = self.vimba.camera(camera_ids[0])

        # Start camera:
        self.cam.open()

        # Set params
        self.cam.Width = self.width
        self.cam.Height = self.height
        self.cam.AcquisitionFrameRate = self.frame_rate
        self.cam.ExposureTime = self.exposure
        self.cam.Gain = self.gain

        self.frame = self.cam.new_frame()
        self.frame.announce()

        self.cam.start_capture()
        self.frame.queue_for_capture()
        self.cam.run_feature_command("AcquisitionStart")

    def read(self):
        """ """
        try:
            self.frame.wait_for_capture(self.timeout_ms)
            self.frame.queue_for_capture()
            frame = self.frame.buffer_data_numpy()
        except VimbaException:
            frame = None
        return frame

    def release(self):
        self.frame.wait_for_capture(self.timeout_ms)
        self.cam.run_feature_command("AcquisitionStop")
        self.cam.end_capture()
        self.cam.revoke_all_frames()
        self.vimba.shutdown()
