from pydra import *
from pydra_modules.cameras.ximea_camera import XimeaModule
from speaker_module import SPEAKER
import os


class TailSaver(VideoSaver):
    name = "tail_camera_saver"

    @staticmethod
    def new_file(directory, filename, ext=""):
        if ext:
            filename = ".".join((filename + "_tail", ext))
        f = os.path.join(directory, filename)
        return f


class JawSaver(VideoSaver):
    name = "jaw_camera_saver"

    @staticmethod
    def new_file(directory, filename, ext=""):
        if ext:
            filename = ".".join((filename + "_jaw", ext))
        f = os.path.join(directory, filename)
        return f


TAIL_CAMERA = XimeaModule.new("tail_camera",
                              saver=TailSaver,
                              camera_params= dict(camera_id=0,
                                                  frame_size=(300, 300),
                                                  frame_rate=300,
                                                  exposure=2000))


JAW_CAMERA = XimeaModule.new("jaw_camera",
                             saver=JawSaver,
                             camera_params= dict(camera_id=1,
                                                 frame_size=(300, 300),
                                                 frame_rate=300,
                                                 exposure=2000))


scanimage = ZMQTrigger(r"tcp://192.168.236.159:5555")


# Add modules to config
config = Configuration(modules=[JAW_CAMERA, TAIL_CAMERA, SPEAKER],
                       triggers={"scanimage": scanimage},
                       gui_params={
                           "directory": r"C:\DATA\Duncan\test",
                           "filename": "test"})


if __name__ == "__main__":
    PydraApp.run(config)
