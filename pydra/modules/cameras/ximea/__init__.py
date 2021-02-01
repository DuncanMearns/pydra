from ..worker import CameraAcquisition


class XimeaCamera(CameraAcquisition):

    name = "ximea"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = 0

    def setup(self):
        """ """
        try:
            from ximea import xiapi
            self.camera = xiapi.Camera(self.id)
        except NameError:
            raise Exception(
                "The xiapi package must be installed to use a Ximea camera!"
            )

        self.camera.open_device()
        self.im = xiapi.Image()

        # If camera supports hardware downsampling (MQ013xG-ON does,
        # MQ003MG-CM does not):
        if self.camera.get_device_name() in [b"MQ013MG-ON", b"MQ013RG-ON", b"MQ013CG-ON"]:
            self.camera.set_sensor_feature_selector("XI_SENSOR_FEATURE_ZEROROT_ENABLE")
            self.camera.set_sensor_feature_value(1)

        self.camera.start_acquisition()
        self.camera.set_acq_timing_mode("XI_ACQ_TIMING_MODE_FRAME_RATE")

    def set_frame_rate(self, fps: float):
        try:
            self.camera.set_framerate(fps)
            return True
        except xiapi.Xi_error:
            return False

    def set_frame_size(self, width: int, height: int):
        try:
            self.camera.set_width(width)
            self.camera.set_height(height)
        except xiapi.Xi_error:
            return False

    def set_offsets(self, x, y):
        try:
            self.camera.set_offsetX(x)
            self.camera.set_offsetY(y)
        except xiapi.Xi_error:
            return False

    def set_exposure(self, ms: int):
        try:
            self.camera.set_exposure(ms * 1000)
        except xiapi.Xi_error:
            return False

    def set_gain(self, gain: int):
        try:
            self.camera.set_gain(gain)
        except xiapi.Xi_error:
            return False

    def read(self):
        try:
            self.camera.get_image(self.im)
            frame = self.im.get_image_data_numpy()
        except xiapi.Xi_error:
            frame = self.empty()
        return frame

    def release(self):
        self.camera.stop_acquisition()
        self.camera.close_device()
