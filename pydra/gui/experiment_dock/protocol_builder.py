from pydra.gui.helpers import TimeUnitWidget
from PyQt5 import QtWidgets, QtCore, QtGui


class SelectionEventHandler(QtCore.QObject):
    """Singleton class that keeps track of which event widget is selected."""

    selectionChanged = QtCore.pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.selectionChanged.connect(self.change_selected)
        self.selected = None

    @QtCore.pyqtSlot(object)
    def change_selected(self, obj):
        self.selected = obj


class EventContainer:
    """Mixin for classes that need to know which event widget is selected."""

    _event_handler = SelectionEventHandler()

    def selected(self):
        return self._event_handler.selected

    def unselect(self):
        self._event_handler.selectionChanged.emit(None)


class FocusWrapper:
    """Wraps Qt focusInEvent, allowing the parent event widget to be selected when child gets focus."""

    def __init__(self, parent, focus_event):
        self.parent = parent
        self.focus_event = focus_event

    def __call__(self, *args, **kwargs):
        self.parent.select()
        self.focus_event(*args, **kwargs)


class EventPicker(QtWidgets.QWidget):

    def __init__(self, event_names, targets=()):
        super().__init__()
        self.event_names = event_names
        self.targets = targets
        self.advanced_options = {"target": "",
                                 "kwargs": {}}
        # Layout
        self.setLayout(QtWidgets.QHBoxLayout())
        self.combo_box = QtWidgets.QComboBox()
        self.combo_box.addItems(event_names)
        self.button = QtWidgets.QPushButton("options...")
        self.button.clicked.connect(self.options_dialog)
        self.layout().addWidget(self.combo_box)
        self.layout().addWidget(self.button)

    @QtCore.pyqtSlot()
    def options_dialog(self):
        # Dialog widget
        dialog = QtWidgets.QDialog(self)
        dialog.setModal(True)
        dialog.setLayout(QtWidgets.QGridLayout())
        # Target
        dialog.layout().addWidget(QtWidgets.QLabel("Target: "), 0, 0)
        combo = QtWidgets.QComboBox()
        combo.addItem("")
        combo.addItems(self.targets)
        target = self.advanced_options["target"]
        combo.setCurrentText(target)
        dialog.layout().addWidget(combo, 0, 1)
        # Kwargs
        table = QtWidgets.QTableWidget(10, 2)
        table.setHorizontalHeaderLabels(("Argument", "Value"))
        for i, (k, v) in enumerate(self.advanced_options["kwargs"].items()):
            table.setItem(i, 0, QtWidgets.QTableWidgetItem(k))
            table.setItem(i, 1, QtWidgets.QTableWidgetItem(v))
        dialog.layout().addWidget(table, 1, 0, 1, 2)
        # Exec
        dialog.exec()
        # Update options
        target = combo.currentText()
        self.advanced_options["target"] = target
        for i in range(table.rowCount()):
            k = table.item(i, 0)
            v = table.item(i, 1)
            # Check key and value are provided
            if k is None:
                continue
            if v is None:
                continue
            key = k.text()
            val = v.text()
            if not key:
                continue
            if not val:
                continue
            self.advanced_options["kwargs"][key] = val


class EventWidget(EventContainer, QtWidgets.QFrame):
    """Widget for adding an event to a protocol"""

    def __init__(self, event_names: tuple = ()):
        super().__init__()
        self.event_names  = event_names
        # Layout
        self.setLayout(QtWidgets.QHBoxLayout())
        self.set_formatting()
        # Enable selection
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self._event_handler.selectionChanged.connect(self.formatSelected)
        # Event widget
        self.event_widgets = [self.wait_widget(), self.event_picker(self.event_names)]
        # Dropdown
        self.dropdown = self.dropdown_widget()
        self.dropdown.currentIndexChanged.connect(self.replaceEventWidget)
        # Add to layout
        self.layout().addWidget(self.dropdown)
        self.layout().addWidget(self.event_widgets[0])
        # Overwrite focus
        for w in [self.dropdown] + self.event_widgets:
            w.focusInEvent = FocusWrapper(self, w.focusInEvent)
            for child in w.findChildren(QtWidgets.QWidget):
                child.focusInEvent = FocusWrapper(self, child.focusInEvent)

    def select(self):
        self._event_handler.selectionChanged.emit(self)

    @QtCore.pyqtSlot(QtGui.QFocusEvent)
    def focusInEvent(self, a0: QtGui.QFocusEvent) -> None:
        self.select()
        super().focusInEvent(a0)

    def set_formatting(self):
        self.setFrameShape(QtWidgets.QFrame.Panel)
        self.setLineWidth(1)
        self.setFrameStyle(self.Box | self.Plain)

    @QtCore.pyqtSlot(object)
    def formatSelected(self, w):
        if w is self:
            self.setLineWidth(2)
        else:
            self.setLineWidth(1)

    @property
    def current_widget(self):
        return self.layout().itemAt(1).widget()

    @QtCore.pyqtSlot(int)
    def replaceEventWidget(self, idx):
        new = self.event_widgets[idx]
        old = self.layout().replaceWidget(self.current_widget, new)
        old.widget().setParent(None)

    @staticmethod
    def dropdown_widget():
        w = QtWidgets.QComboBox()
        w.addItems(["wait", "event"])
        return w

    @staticmethod
    def wait_widget():
        w = TimeUnitWidget()
        w.addMilliseconds(minval=1, maxval=999)
        w.addSeconds(minval=1, maxval=999)
        w.addMinutes(minval=1, maxval=999)
        return w

    @staticmethod
    def event_picker(event_names):
        w = EventPicker(event_names)
        return w


class ProtocolBuilder(EventContainer, QtWidgets.QWidget):

    def __init__(self, event_names):
        super().__init__()
        self.event_names = event_names
        self.events = []
        # Layout
        self.setLayout(QtWidgets.QVBoxLayout())
        # Event window
        self.event_window = QtWidgets.QWidget()
        self.event_window.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.event_window)
        # Buttons
        self.buttons_container = QtWidgets.QWidget()
        self.buttons_container.setLayout(QtWidgets.QHBoxLayout())
        self.ADD = QtWidgets.QPushButton("+")
        self.ADD.clicked.connect(self.addEvent)
        self.DEL = QtWidgets.QPushButton("-")
        self.DEL.clicked.connect(self.removeEvent)
        self.DEL.setEnabled(False)
        self.buttons_container.layout().addWidget(self.ADD)
        self.buttons_container.layout().addWidget(self.DEL)
        self.layout().addWidget(self.buttons_container)

    @QtCore.pyqtSlot()
    def addEvent(self):
        new_event = EventWidget(self.event_names)
        new_event.select()
        self.events.append(new_event)
        self.event_window.layout().addWidget(new_event)
        self.DEL.setEnabled(True)

    @QtCore.pyqtSlot()
    def removeEvent(self):
        w = self.selected()
        if w:
            self.events.remove(w)
            w.setParent(None)
            self.unselect()
        if not len(self.events):
            self.DEL.setEnabled(False)
