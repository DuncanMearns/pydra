from ..classes import Worker, Saver
from ..gui.public import *
import typing


class PydraModule:

    def __init__(self,
                 worker: typing.Type[Worker],
                 params: typing.Mapping = None,
                 saver: typing.Type[Saver] = None,
                 widget: typing.Type[ControlWidget] = None,
                 plotter: typing.Type[Plotter] = None,
                 threaded: bool = False,
                 **kwargs):
        self.worker = worker
        self.params = params
        self.saver = saver
        self.widget = widget
        self.plotter = plotter
        self.threaded = threaded
        for k, val in kwargs.keys():
            setattr(self, k, val)

    def __getitem__(self, item):
        try:
            return getattr(self, item)
        except AttributeError:
            raise KeyError(f"PydraModule has no {item} key.")

    @property
    def params(self) -> dict:
        return self._params

    @params.setter
    def params(self, _params: typing.Mapping):
        self._params = {}
        if _params:
            self._params.update(_params)

    @property
    def saver(self) -> typing.Union[typing.Type[Saver], None]:
        try:
            return self._saver
        except AttributeError:
            return None

    @saver.setter
    def saver(self, _saver):
        if _saver:
            self._saver = _saver
            self._saver.add_worker(self.worker)

    @property
    def name(self):
        return self.worker.name

    @property
    def gui_events(self):
        return self.worker.gui_events
