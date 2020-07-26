from PyQt5 import QtCore, QtGui, QtWidgets


class PluginWidget(QtWidgets.QDockWidget):

    def __init__(self, plugin, *args, **kwargs):
        super().__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)
        self.plugin = plugin
        self.setMinimumWidth(250)
        self.setFeatures(QtGui.QDockWidget.NoDockWidgetFeatures)
        self.setWidget(QtWidgets.QWidget())
        self.widget().setLayout(QtWidgets.QGridLayout())
        self.widget().layout().setAlignment(QtCore.Qt.AlignTop)
