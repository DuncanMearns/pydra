from pydra.gui.helpers import SignalProxy, TimeUnitWidget
from pydra.protocol import events
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


class ChangesProtocol:
    """Mixin for classes that can modify the protocol by allowing them to emit a 'changed' signal."""
    _protocol_change_proxy = SignalProxy()

    @QtCore.pyqtSlot()
    def changed(self, *args):  # eat arguments from any connected signals
        self._protocol_change_proxy.emit()


class FocusWrapper:
    """Wraps Qt focusInEvent, allowing the parent event widget to be selected when child gets focus."""

    def __init__(self, parent, focus_event):
        self.parent = parent
        self.focus_event = focus_event

    def __call__(self, *args, **kwargs):
        self.parent.select()
        self.focus_event(*args, **kwargs)


class WaitWidget(ChangesProtocol, TimeUnitWidget):

    def __init__(self):
        super().__init__()
        self.addMilliseconds(minval=1, maxval=999)
        self.addSeconds(minval=1, maxval=999)
        self.addMinutes(minval=1, maxval=999)
        self.valueChanged.connect(self.changed)

    def to_event(self):
        return events.PAUSE(self.value / 1000.)


class EventPicker(ChangesProtocol, QtWidgets.QWidget):

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
        self.combo_box.currentIndexChanged.connect(self.changed)

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
        self.changed()  # emits the protocol changed signal

    def to_event(self):
        event_name = self.combo_box.currentText()
        event_kw = self.advanced_options["kwargs"]
        target = self.advanced_options["target"]
        if target:
            event_kw["target"] = target
        return events.EVENT(event_name, event_kw)


class EventWidget(ChangesProtocol, EventContainer, QtWidgets.QFrame):
    """Widget for adding an event to a protocol"""

    def __init__(self, event_names: tuple = ()):
        super().__init__()
        self.event_names = event_names
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
        self.changed()  # emits the changed signal

    @staticmethod
    def dropdown_widget():
        w = QtWidgets.QComboBox()
        w.addItems(["wait", "event"])
        return w

    @staticmethod
    def wait_widget():
        w = WaitWidget()
        return w

    @staticmethod
    def event_picker(event_names):
        w = EventPicker(event_names)
        return w

    def to_event(self):
        return self.current_widget.to_event()


class ProtocolBuilder(ChangesProtocol, EventContainer, QtWidgets.QWidget):

    protocol_changed = QtCore.pyqtSignal(list)

    def __init__(self, event_names):
        super().__init__()
        self.event_names = event_names
        self.event_widgets = []
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
        # Catch any changes to protocol
        self._protocol_change_proxy.connect(self.update_protocol)

    @QtCore.pyqtSlot()
    def addEvent(self):
        new_event = EventWidget(self.event_names)
        new_event.select()
        self.event_widgets.append(new_event)
        self.event_window.layout().addWidget(new_event)
        self.DEL.setEnabled(True)
        self.changed()  # emits the changed signal

    @QtCore.pyqtSlot()
    def removeEvent(self):
        w = self.selected()
        if w:
            self.event_widgets.remove(w)
            w.setParent(None)
            self.unselect()
        if not len(self.event_widgets):
            self.DEL.setEnabled(False)
        self.update_protocol()
        self.changed()  # emits the changed signal

    def to_protocol(self):
        return [w.to_event() for w in self.event_widgets]

    @QtCore.pyqtSlot()
    def update_protocol(self):
        self.protocol_changed.emit(self.to_protocol())
