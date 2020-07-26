from PyQt5 import QtCore


class StateEnabled:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @QtCore.pyqtSlot()
    def idle(self):
        pass

    @QtCore.pyqtSlot()
    def live(self):
        pass

    @QtCore.pyqtSlot()
    def record(self):
        pass
