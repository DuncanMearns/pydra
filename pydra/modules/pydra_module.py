from .._base.pydra_object import PydraType
from ..classes import Worker
from ..gui.public import UserWidgetType
from ..utils.parameterized import Parameterized


class PydraModule(Parameterized, worker=Worker, params={}, threaded=False):

    def __init__(self,
                 worker: PydraType,
                 params: dict = None,
                 saver: PydraType = None,
                 widget: UserWidgetType = None,
                 plotter: UserWidgetType = None,
                 **kwargs):
        super().__init__()
        # Set mandatory attributes
        self.worker = worker
        if params:
            self.params = params
        # Set optional attributes
        self.saver = saver
        if self.saver:
            self.saver.add_worker(self.name)
        self.widget = widget
        self.plotter = plotter
        for k, val in kwargs.keys():
            setattr(self, k, val)

    @property
    def name(self):
        return self.worker.name

    @property
    def gui_events(self):
        return self.worker.gui_events
