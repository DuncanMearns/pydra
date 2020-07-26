from PyQt5 import QtWidgets


class PluginWidget(QtWidgets.QDockWidget):

    def __init__(self, plugin, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plugin = plugin
