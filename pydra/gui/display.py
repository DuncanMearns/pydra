from PyQt5 import QtWidgets
from pyqtgraph.dockarea import DockArea, Dock


class DisplayContainer(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLayout(QtWidgets.QVBoxLayout())
        self._dock_area = DockArea()
        self.layout().addWidget(self._dock_area)
        self.plotters = {}

    def add(self, name: str, widget) -> None:
        dock = Dock(name)
        dock.addWidget(widget)
        self.plotters[name] = widget
        self._dock_area.addDock(dock)
