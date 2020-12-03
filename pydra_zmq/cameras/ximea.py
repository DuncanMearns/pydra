from .camera import CameraAcquisition
from ..core.messaging import logged


class XimeaCamera(CameraAcquisition):

    name = "ximea"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setup(self):
        """ """
        try:
            from ximea import xiapi
            self.camera = xiapi.Camera()
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

    @logged
    def set_params(self, **kwargs):
        new_params = {}
        if "exposure" in kwargs:
            self.camera.set_exposure(int(kwargs["exposure"] * 1000))
            new_params["exposure"] = kwargs["exposure"]
        if "frame_rate" in kwargs:
            self.camera.set_framerate(kwargs["frame_rate"])
            new_params["frame_rate"] = kwargs["frame_rate"]
        if "frame_size" in kwargs:
            w, h = kwargs["frame_size"]
            self.camera.set_width(w)
            self.camera.set_height(h)
            new_params["frame_size"] = (w, h)
        if "offset" in kwargs:
            x, y = kwargs["offset"]
            self.camera.set_offsetX(x)
            self.camera.set_offsetY(y)
            new_params["offset"] = (x, y)
        if "gain" in kwargs:
            self.camera.set_gain(kwargs["gain"])
            new_params["gain"] = kwargs["gain"]
        return new_params

    def read(self):
        try:
            self.camera.get_image(self.im)
            frame = self.im.get_image_data_numpy()
        except xiapi.Xi_error:
            frame = None
        return frame

    def release(self):
        self.camera.stop_acquisition()
        self.camera.close_device()
