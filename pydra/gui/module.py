from .states import StateEnabled
from PyQt5 import QtWidgets, QtGui


class ModuleWidget(QtWidgets.QDockWidget, StateEnabled):

    def __init__(self, name, parent, *args, **kwargs):
        super().__init__(name, parent)
        self.setMinimumWidth(250)
        self.setMinimumHeight(100)
        self.setMaximumHeight(300)
        self.name = name
        # Add to parent window menu
        self.displayAction = QtWidgets.QAction(name, self.parent())
        self.displayAction.setCheckable(True)
        self.displayAction.setChecked(True)
        self.displayAction.triggered.connect(self.show_window)
        self.parent().windowMenu.addAction(self.displayAction)

    def show_window(self, state):
        if state:
            self.show()
        else:
            self.close()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.displayAction.setChecked(False)
        event.accept()

    def send_event(self, event_name, **kwargs):
        self.parent().pydra.send_event(event_name, target=self.name, **kwargs)

    def updateData(self, **params):
        return
