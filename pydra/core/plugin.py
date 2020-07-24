from PyQt5 import QtCore


class Plugin(QtCore.QObject):

    name = ''
    worker = None
    widget = None

    def __init__(self, pydra, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pydra = pydra
        self.params = {}

    def to_tuple(self):
        return self.name, self.worker, self.params
