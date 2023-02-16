from pydra import *
from pydra_modules.cameras.ximea_camera import XimeaModule
from pydra.modules.visual_stimulation import VisualStimulationModule
import os
from datetime import datetime


class EyeSaver(VideoSaver):
    name = "eye_camera_saver"

    @staticmethod
    def new_file(directory, filename, ext=""):
        if ext:
            filename = ".".join((filename + "eye", ext))
        f = os.path.join(directory, filename)
        return f


PROJECTOR = VisualStimulationModule(stimulus_file=r'C:\Users\lbauer\Documents\GitHub\hyperion_experiment_control\new_pydra_20210825\pseudo_saccade_stimulus.py',
                                    window_params=dict(monitor=u'Lisa_Monitor'))


EYE_CAMERA = XimeaModule.new("eye_camera",
                             saver=EyeSaver,
                             camera_params=dict(camera_id=0,
                                                frame_size=(300, 300),
                                                frame_rate=300,
                                                exposure=2000))


scanimage = ZMQTrigger(r"tcp://192.168.236.116:5559")

Fish_number = 0
experiment_type = "test"

# Add modules to config
config = Configuration(modules=[PROJECTOR],  #, EYE_CAMERA],
                       triggers={"scanimage": scanimage},
                       gui_params={
                           "directory": fr"F:\Lisa\{datetime.today().strftime('%Y%m%d')}",
                           "filename": f"{datetime.today().strftime('%Y%m%d')}_Fish{Fish_number}_{experiment_type}"})

if __name__ == "__main__":
    PydraApp.run(config)