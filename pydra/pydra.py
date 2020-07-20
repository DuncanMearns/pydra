from .pipeline import Experiment

from .acquisition import CameraAcquisition
from .acquisition.cameras import PikeCamera

from .tracking import DummyTracker
from .saving import VideoSaver, NoSaver

from .plugins.optogenetics import Optogenetics, OptogeneticsProtocol
import pandas as pd


class Pydra:

    # acquisition_modes = dict(
    #     pike=(CameraAcquisition, {'camera_type': PikeCamera})
    # )
    #
    # tracking_modes = dict(
    #     none=(DummyTracker, {})
    # )
    #
    # saving_modes = dict(
    #     none=(NoSaver, {}),
    #     video=(VideoSaver, {'video_path': r"E:\Duncan\test.avi"})
    # )

    def __init__(self):

        # ====================================
        # ACQUISITION-TRACKING-SAVING PIPELINE
        # ====================================

        self.acquisition = CameraAcquisition
        self.acquisition_kw = {'camera_type': PikeCamera}

        self.tracking = DummyTracker
        self.tracking_kw = {}

        self.saving = NoSaver
        self.saving_kw = {}

        self.stimulus_df = pd.DataFrame(dict(t=[1, 4, 7, 10], stim=[1, 0, 1, 0]))
        self.protocol = OptogeneticsProtocol
        self.protocol_kw = {'stimulus_df': self.stimulus_df}

    def start(self):
        self.pipeline = Experiment(self.acquisition, self.acquisition_kw,
                                   self.tracking, self.tracking_kw,
                                   self.saving, self.saving_kw,
                                   self.protocol, self.protocol_kw)
        self.pipeline.start()

    def stop(self):
        self.pipeline.stop()
