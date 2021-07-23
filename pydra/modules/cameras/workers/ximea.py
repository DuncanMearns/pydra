try:
    from ximea import xiapi
except NameError:
    raise Exception(
        "The xiapi package must be installed to use a Ximea camera!"
    )
from pydra.modules.cameras.workers._base import CameraAcquisition


class XimeaCamera(CameraAcquisition):

    name = "ximea"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = 0
        self.frame = None

    def setup(self):
        self.camera = xiapi.Camera(self.id)
        self.camera.open_device()
        self.frame = xiapi.Image()

        # If camera supports hardware downsampling (MQ013xG-ON does,
        # MQ003MG-CM does not):
        if self.camera.get_device_name() in [b"MQ013MG-ON", b"MQ013RG-ON", b"MQ013CG-ON"]:
            self.camera.set_sensor_feature_selector("XI_SENSOR_FEATURE_ZEROROT_ENABLE")
            self.camera.set_sensor_feature_value(1)

        self.camera.start_acquisition()
        self.camera.set_acq_timing_mode("XI_ACQ_TIMING_MODE_FRAME_RATE")
        try:
            self.camera.set_downsampling("XI_DWN_2x2")
        except xiapi.Xi_error:
            pass
        self.set_params(
            frame_size=self.frame_size,
            frame_rate=self.frame_rate,
            exposure=self.exposure,
            gain=self.gain
        )

    def set_frame_rate(self, fps: float) -> bool:
        try:
            self.camera.set_framerate(fps)
            return super().set_frame_rate(fps)
        except xiapi.Xi_error:
            return False

    def set_frame_size(self, width: int, height: int) -> bool:
        try:
            self.camera.set_width(width)
            self.camera.set_height(height)
            return super().set_frame_size(width, height)
        except xiapi.Xi_error:
            return False

    def set_offsets(self, x: int, y: int) -> bool:
        try:
            self.camera.set_offsetX(x)
            self.camera.set_offsetY(y)
            return super().set_frame_size(x, y)
        except xiapi.Xi_error:
            return False

    def set_exposure(self, u: int) -> bool:
        try:
            self.camera.set_exposure(u)
            return super().set_exposure(u)
        except xiapi.Xi_error:
            return False

    def set_gain(self, gain: float) -> bool:
        try:
            self.camera.set_gain(gain)
            return super().set_gain(gain)
        except xiapi.Xi_error:
            return False

    def read(self):
        try:
            self.camera.get_image(self.frame)
            frame = self.frame.get_image_data_numpy()
        except xiapi.Xi_error:
            frame = self.empty()
        return frame

    def cleanup(self):
        self.camera.stop_acquisition()
        self.camera.close_device()
