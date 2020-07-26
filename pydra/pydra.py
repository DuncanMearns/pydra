from .handler import Handler

from .cameras import PikeCamera
from .tracking import NoTracking
from .saving import VideoSaver
from .stimulation.optogenetics import Optogenetics


class Pydra:

    config = {
        'acquisition': PikeCamera,
        'tracking': NoTracking,
        'saving': VideoSaver,
        'protocol': Optogenetics
    }

    def __init__(self):
        self.acquisition = self.config['acquisition'](self)
        self.tracking = self.config['tracking'](self)
        self.saving = self.config['saving'](self)
        self.protocol = self.config['protocol'](self)

        self.handler = Handler(self.acquisition.to_tuple(),
                               self.tracking.to_tuple(),
                               self.saving.to_tuple(),
                               self.protocol.to_tuple())
        self._start_processes()

    def _start_processes(self):
        self.handler.start()

    def _join_processes(self):
        self.handler.exit()

    def start(self):
        self.handler.start_event_loop()
        # self.pipeline.protocol_sender.send(dict(stimulus_df=pd.DataFrame(dict(t=[0, 1, 2], stimulation=[0, 1, 0]))))
        # time.sleep(0.1)
        # self.handler.start_protocol_event_loop()

    def stop(self):
        self.handler.stop_event_loop()
