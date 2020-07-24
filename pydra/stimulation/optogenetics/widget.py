from PyQt5 import QtWidgets, QtCore


class OptogeneticsWidget(QtWidgets.QWidget):

    def __init__(self, optogenetics, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.optogenetics = optogenetics
