"""
Module containing the PydraModule class.
"""
from ..base import Worker, Saver
from ..gui.public import ControlWidget, Plotter
import typing


class PydraModule:

    def __init__(self,
                 worker: typing.Type[Worker],
                 worker_args: tuple = (),
                 worker_kwargs: typing.Mapping = None,
                 saver: typing.Type[Saver] = None,
                 widget: typing.Type[ControlWidget] = None,
                 plotter: typing.Type[Plotter] = None,
                 threaded: bool = False,
                 **kwargs):
        self.worker = worker
        self.worker_args = worker_args
        self.worker_kwargs = worker_kwargs or {}
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
    def name(self) -> str:
        return self.worker.name

    @property
    def worker(self) -> typing.Type[Worker]:
        return self._worker

    @worker.setter
    def worker(self, worker_cls: typing.Type[Worker]):
        self._worker = worker_cls

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
            self._saver.new_subscription(self.worker)

    @property
    def gui_events(self):
        return self.worker.gui_events
