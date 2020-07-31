from PyQt5 import QtCore


class Plugin(QtCore.QObject):

    name = ''
    worker = None
    params = {}
    widget = None
    plotter = None

    paramsChanged = QtCore.pyqtSignal(str, object)

    def __init__(self, pydra, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pydra = pydra

    @classmethod
    def to_tuple(cls):
        return cls.name, cls.worker, dict(cls.params)  # must make copy of class params
