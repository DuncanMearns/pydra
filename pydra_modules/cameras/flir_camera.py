try:
    from simple_pyspin import Camera as PySpinCam
    from simple_pyspin import CameraError
    from PySpin import SpinnakerException
except NameError:
    raise Exception(
        "The PySpin and simple_pyspin packages must be installed to use a Flir camera!"
    )
from pydra.modules.camera import CameraModule, Camera, setter


class FlirCamera(Camera):

    camera_exception = CameraError

    def __init__(self, *args, camera_id=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.camera_id = camera_id
        self.frame = None

    def setup(self):
        self.camera = PySpinCam(self.camera_id)  # Acquire Camera
        self.camera.init()  # Initialize camera
        # Enable manual frame rate control
        self.camera.AcquisitionFrameRateAuto = 'Off'
        self.camera.AcquisitionFrameRateEnabled = True
        # Enable manual gain control
        self.camera.GainAuto = 'Off'
        # Enable manual exposure control
        self.camera.ExposureAuto = 'Off'
        # Start the camera
        self.camera.start()

    def read(self):
        try:
            frame = self.camera.get_array()
        except:
            frame = self.empty()
        return frame

    def shutdown(self):
        if self.camera:
            self.camera.stop()  # Stop recording
            self.camera.close()  # You should explicitly clean up

    # def frame_rate(self, fps: float):
    #     self.camera.AcquisitionFrameRate = fps

    @setter
    def frame_rate(self, fps: float):
        self.camera.stop()
        try:
            self.camera.AcquisitionFrameRate = fps
        except SpinnakerException as e:
            print(e)
        except TypeError:
            pass
        self.camera.start()
        return self.camera.AcquisitionFrameRate

    @setter
    def frame_size(self, wh: tuple):
        self.camera.stop()
        try:
            width, height = wh
            self.camera.Width = width
            self.camera.Height = height
        except SpinnakerException as e:
            print(e)
        except TypeError:
            pass
        self.camera.start()
        return self.camera.Width, self.camera.Height

    @setter
    def offsets(self, xy: tuple):
        self.camera.stop()
        try:
            x, y = xy
            self.camera.OffsetX = x
            self.camera.OffsetY = y
        except SpinnakerException as e:
            print(e)
        except TypeError:
            pass
        self.camera.start()
        return self.camera.OffsetX , self.camera.OffsetY

    @setter
    def exposure(self, u: int):
        self.camera.stop()
        try:
            self.camera.ExposureTime = u  # microseconds
        except SpinnakerException as e:
            print(e)
        except TypeError:
            pass
        self.camera.start()
        return self.camera.ExposureTime

    @setter
    def gain(self, val: float):
        self.camera.stop()
        try:
            self.camera.Gain = val
        except SpinnakerException as e:
            print(e)
        except TypeError:
            pass
        self.camera.start()
        return self.camera.Gain


class FlirModule(CameraModule):
    camera = FlirCamera


def test_flir():
    from pydra import PydraApp, Configuration
    FLIR = FlirModule.new("flir")
    config = Configuration(modules=[FLIR])
    PydraApp.run(config)


if __name__ == "__main__":
    test_flir()
