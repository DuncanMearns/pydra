from .pipeline import Pipeline

from .acquisition import CameraAcquisition
from .acquisition.cameras import PikeCamera

from .tracking import DummyTracker
from .saving import NoSaver

from .core import pipe
from .plugins.protocols import ProtocolProcess
from .plugins.optogenetics.optogenetics import StimulationProtocol, Optogenetics
from threading import Event
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

        # ========
        # PROTOCOL
        # ========
        self.protocol = Optogenetics

    def run(self):
        self.pipeline = Pipeline(self.acquisition, self.acquisition_kw,
                                 self.tracking, self.tracking_kw,
                                 self.saving, self.saving_kw, self.protocol)
        self.pipeline.run()

    def start_pipeline(self):
        self.pipeline.start()
        # self.conn.send(stimulus_df=pd.DataFrame(dict(t=[0, 1, 2], stimulation=[0, 1, 0])))
        # self.protocol_process.start_flag.set()

    def stop_pipeline(self):
        self.pipeline.stop()

    def terminate(self):
        self.pipeline.exit()
