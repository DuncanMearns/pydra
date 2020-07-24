from .pipeline import Pipeline

from .acquisition import CameraAcquisition
from .acquisition.cameras import PikeCamera

from .tracking import DummyTracker
from .saving import NoSaver

from pydra.stimulation.optogenetics import OptogeneticsProtocol
import pandas as pd
import time


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

        # ========
        # PROTOCOL
        # ========
        self.protocol = OptogeneticsProtocol

    def start_pipeline(self):
        self.pipeline = Pipeline(self.acquisition, self.acquisition_kw,
                                 self.tracking, self.tracking_kw,
                                 self.saving, self.saving_kw, self.protocol, {})
        self.pipeline.start()

    def start(self):
        self.pipeline.start_event_loop()
        self.pipeline.protocol_sender.send(dict(stimulus_df=pd.DataFrame(dict(t=[0, 1, 2], stimulation=[0, 1, 0]))))
        time.sleep(0.1)
        self.pipeline.start_protocol_event_loop()

    def stop(self):
        self.pipeline.stop_event_loop()

    def stop_pipeline(self):
        self.pipeline.exit()
