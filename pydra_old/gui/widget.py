from PyQt5 import QtCore, QtGui, QtWidgets
from .state import StateEnabled


class PluginWidget(StateEnabled, QtWidgets.QDockWidget):

    def __init__(self, plugin, *args, **kwargs):
        super().__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)
        self.plugin = plugin
        self.setMinimumWidth(250)
        self.setMinimumHeight(100)
        self.setMaximumHeight(300)
        self.setFeatures(QtGui.QDockWidget.NoDockWidgetFeatures)
        self.setWidget(QtWidgets.QWidget())
        self.widget().setLayout(QtWidgets.QGridLayout())
        self.widget().layout().setAlignment(QtCore.Qt.AlignTop)
