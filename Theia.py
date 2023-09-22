from pydra import *
from pydra_modules.cameras.ximea_camera import XimeaModule
from pydra.modules.visual_stimulation import VisualStimulationModule
import os
from datetime import datetime
from psychopy import monitors


my_monitor = monitors.Monitor(u'Lisa_Monitor')
screen_size = my_monitor.getSizePix()
units = 'degFlat'

PROJECTOR = VisualStimulationModule(
    stimulus_file=r'C:\Users\lbauer\Documents\GitHub\pydra\visual_stimuli\pseudo_saccade_stimulus.py',
    window_params=dict(size=screen_size,
                       fullscr=False,
                       units=units,
                       color=(-1, -1, -1),
                       allowGUI=True,
                       allowStencil=False,
                       monitor=u'Lisa_Monitor',
                       colorSpace=u'rgb',
                       blendMode=u'avg',
                       useFBO=True,
                       screen=1))

EYE_CAMERA = XimeaModule.new("eye_camera",
                             camera_params=dict(camera_id=0,
                                                frame_size=(2000, 2000),
                                                frame_rate=30,
                                                exposure=2000))

scanimage = ZMQTrigger(r"tcp://192.168.236.116:5559")

Fish_number = 96
experiment_number = 1
experiment_type = "circleJJ"

# Add modules to config
config = Configuration(modules=[EYE_CAMERA, PROJECTOR],
                       triggers={"scanimage": scanimage},
                       gui_params={
                           "directory": fr"F:\Lisa\{datetime.today().strftime('%Y%m%d')}",
                           "filename": f"{datetime.today().strftime('%Y%m%d')}_fish{Fish_number}_00{experiment_number}_{experiment_type}"})

if __name__ == "__main__":
    PydraApp.run(config)
