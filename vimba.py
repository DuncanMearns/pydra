try:
    from pymba import Vimba
    from pymba.vimbaexception import VimbaException
except ImportError:
    pass


class PikeCamera:
    """Class for controlling an AVT camera.
    Uses the Vimba interface pymba
    (module documentation `here <https://github.com/morefigs/pymba>`_).
    Parameters
    ----------
    Returns
    -------
    """

    def __init__(self, **kwargs):
        # Set timeout for frame acquisition. Give this as input?
        self.timeout_ms = 1000

        super().__init__(**kwargs)

        try:
            self.vimba = Vimba()
        except NameError:
            raise Exception("The pymba package must be installed to use an AVT camera!")

        self.frame = None

    def open_camera(self):
        """ """
        self.vimba.startup()

        camera_ids = self.vimba.camera_ids()
        self.cam = self.vimba.camera(camera_ids[0])

        # Start camera:
        self.cam.open()
        self.frame = self.cam.new_frame()
        self.frame.announce()

        self.cam.start_capture()
        self.frame.queue_for_capture()
        self.cam.run_feature_command("AcquisitionStart")

    def set(self, param, val):
        """
        Parameters
        ----------
        param :
        val :
        Returns
        -------
        """
        messages = []
        try:
            if param == "exposure":
                # camera wants exposure in us:
                self.cam.ExposureTime = int(val * 1000)

            else:
                # To set new frame rate for AVT cameras acquisition has to be
                # interrupted:
                messages.append("E:" + param + " setting not supported on AVT cameras")
        except VimbaException:
            messages.append("E:Invalid value! {} will not be changed.".format(param))
        return messages

    def read(self):
        """ """
        try:
            self.frame.wait_for_capture(self.timeout_ms)
            self.frame.queue_for_capture()

            frame = self.frame.buffer_data_numpy()

            # frame = np.ndarray(
            #     buffer=raw_data,
            #     dtype=np.uint8,
            #     shape=(self.frame.height, self.frame.width),
            # )

        except VimbaException:
            frame = None

        return frame

    def release(self):
        """ """
        self.frame.wait_for_capture(self.timeout_ms)
        self.cam.run_feature_command("AcquisitionStop")
        self.cam.end_capture()
        self.cam.revoke_all_frames()
        self.vimba.shutdown()
