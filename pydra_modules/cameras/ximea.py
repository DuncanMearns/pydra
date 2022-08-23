try:
    from ximea import xiapi
except NameError:
    raise Exception(
        "The xiapi package must be installed to use a Ximea camera!"
    )
from pydra.modules.acquisition.camera import Camera, setter, CAMERA


class XimeaCamera(Camera):

    def __init__(self, *args, camera_id=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.camera_id = camera_id
        self.frame = None

    def setup(self):
        self.camera = xiapi.Camera(self.camera_id)
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
        self.set_params(**self.params)

    def read(self):
        try:
            self.camera.get_image(self.frame, timeout=1)
            frame = self.frame.get_image_data_numpy()
        except xiapi.Xi_error:
            frame = self.empty()
        return frame

    def shutdown(self):
        self.camera.stop_acquisition()
        self.camera.close_device()

    @setter
    def frame_rate(self, fps: float):
        try:
            self.camera.set_framerate(fps)
        except xiapi.Xi_error as e:
            print(e)
        except TypeError:
            pass
        return self.camera.get_framerate()

    @setter
    def frame_size(self, wh: tuple):
        try:
            width, height = wh
            self.camera.set_width(width)
            self.camera.set_height(height)
        except xiapi.Xi_error as e:
            print(e)
        except TypeError:
            pass
        return self.camera.get_width(), self.camera.get_height()

    @setter
    def offsets(self, xy: tuple):
        try:
            x, y = xy
            self.camera.set_offsetX(x)
            self.camera.set_offsetY(y)
        except xiapi.Xi_error as e:
            print(e)
        except TypeError:
            pass
        return self.camera.get_offsetX(), self.camera.get_offsetY()

    @setter
    def exposure(self, u: int):
        try:
            self.camera.set_exposure(u)
        except xiapi.Xi_error as e:
            print(e)
        except TypeError:
            pass
        return self.camera.get_exposure()

    @setter
    def gain(self, val: float):
        try:
            self.camera.set_gain(val)
        except xiapi.Xi_error as e:
            print(e)
        except TypeError:
            pass
        return self.camera.get_gain()


XIMEA = dict(CAMERA)
XIMEA["worker"].name = "ximea"
XIMEA["params"]["camera_type"] = XimeaCamera
