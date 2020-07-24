from PyQt5 import QtCore


class Plugin(QtCore.QObject):

    acquisition = None
    tracker = None
    saver = None
    protocol = None
    widget = None

    def __init__(self, pipeline, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pipeline = pipeline
