from ..core.base import PydraProcess, pipe
from threading import Event
from PyQt5 import QtCore


class Plugin(QtCore.QObject):

    protocol = None
    widget = None

    def __init__(self, pipeline, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pipeline = pipeline
