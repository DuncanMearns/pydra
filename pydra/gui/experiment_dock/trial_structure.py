"""Module containing widgets for handling and building protocols."""
import warnings
from PyQt5 import QtWidgets, QtCore, QtGui
from ast import literal_eval
from datetime import datetime
import json
import os
import re

from ..state_machine import Stateful
from ..helpers import SignalProxy, TimeUnitWidget
from ...protocol import events


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
    """Widget that allows a pause to be introduced into a protovol."""

    def __init__(self):
        super().__init__()
        self.addMilliseconds(minval=1, maxval=999)
        self.addSeconds(minval=1, maxval=999)
        self.addMinutes(minval=1, maxval=999)
        self.valueChanged.connect(self.changed)

    def to_event(self):
        return events.PAUSE(self.value / 1000.)


class EventPicker(ChangesProtocol, QtWidgets.QWidget):
    """Widget the allows Pydra events to be defined in a protocol."""

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
        self.advanced_options["kwargs"] = {}  # re-create advanced options dictionary
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

    @staticmethod
    def evaluate_string(s: str):
        try:
            if any([char.isdigit() for char in s]):
                return literal_eval(s)
            if any([char in s for char in "{}()[],"]):
                return literal_eval(s)
        except ValueError:
            warnings.warn(f"Could not parse value: {s}")
        return s

    def to_event(self):
        event_name = self.combo_box.currentText()
        event_kw = dict([(k, self.evaluate_string(val)) for k, val in self.advanced_options["kwargs"].items()])
        target = self.advanced_options["target"]
        if target:
            event_kw["target"] = target
        return events.EVENT(event_name, event_kw)


class EventWidget(ChangesProtocol, EventContainer, QtWidgets.QFrame):
    """A widget for that is added to and shown in the ProtocolBuilder."""

    def __init__(self, event_names: tuple = (), targets: tuple=()):
        super().__init__()
        self.event_names = event_names
        self.targets = targets
        # Layout
        self.setLayout(QtWidgets.QHBoxLayout())
        self.set_formatting()
        # Enable selection
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self._event_handler.selectionChanged.connect(self.formatSelected)
        # Event widget
        self.event_widgets = [self.wait_widget(), self.event_picker(self.event_names, self.targets)]
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
    def event_picker(event_names, targets):
        w = EventPicker(event_names, targets=targets)
        return w

    def to_event(self):
        return self.current_widget.to_event()


class ProtocolBuilder(ChangesProtocol, EventContainer, QtWidgets.QWidget):
    """The widget for showing, adding, and removing events from a protocol."""

    def __init__(self, event_names, targets=()):
        super().__init__()
        self.event_names = event_names
        self.targets = targets
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

    @QtCore.pyqtSlot()
    def addEvent(self):
        new_event = EventWidget(self.event_names, self.targets)
        new_event.select()
        self.event_widgets.append(new_event)
        self.event_window.layout().addWidget(new_event)
        self.DEL.setEnabled(True)
        self.changed()  # emits the changed signal
        return new_event

    @QtCore.pyqtSlot()
    def removeEvent(self):
        w = self.selected()
        if w:
            self.event_widgets.remove(w)
            w.setParent(None)
            self.unselect()
        if not len(self.event_widgets):
            self.DEL.setEnabled(False)
        self.changed()  # emits the changed signal

    def to_protocol(self):
        return [w.to_event() for w in self.event_widgets]


class ProtocolTab(ChangesProtocol, Stateful, QtWidgets.QWidget):
    """Tab for creating, saving, and loading protocols."""

    def __init__(self, event_names: tuple, targets=()):
        super().__init__()
        # Layout
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        # -----------
        # REPETITIONS
        # -----------
        self.reps_widget = QtWidgets.QWidget()
        self.reps_widget.setLayout(QtWidgets.QHBoxLayout())
        self.reps_widget.layout().setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        # Repetitions
        self.reps_label = QtWidgets.QLabel("N reps:")
        self.reps_label.setToolTip("Number of repetitions of the protocol within a trial")
        self.reps_spinbox = QtWidgets.QSpinBox()
        self.reps_spinbox.setMinimum(1)
        self.reps_spinbox.setMaximum(999)
        self.reps_spinbox.setValue(1)
        self.reps_spinbox.valueChanged.connect(self.changed)
        # Interval
        self.interval_label = QtWidgets.QLabel("Interval:")
        self.interval_label.setToolTip("Time between protocol repetitions")
        self.interval_widget = TimeUnitWidget()
        self.interval_widget.addMilliseconds(minval=0, maxval=60_000)
        self.interval_widget.addSeconds(minval=0, maxval=600)
        self.interval_widget.addMinutes(minval=0, maxval=300)
        self.interval_widget.valueChanged.connect(self.changed)
        # Add to layout
        self.reps_widget.layout().addWidget(self.reps_label)
        self.reps_widget.layout().addWidget(self.reps_spinbox)
        self.reps_widget.layout().addWidget(self.interval_label)
        self.reps_widget.layout().addWidget(self.interval_widget)
        self.layout().addWidget(self.reps_widget)
        # -------
        # DIVIDER
        # -------
        self.layout().addWidget(self.divider())
        # -------
        # BUILDER
        # -------
        self.builder_widget = ProtocolBuilder(event_names, targets=targets)
        self.layout().addWidget(self.builder_widget)
        # -----------
        # SAVE / LOAD
        # -----------
        self.layout().addWidget(self.divider())
        self.SAVE = QtWidgets.QPushButton("SAVE")
        self.SAVE.clicked.connect(self.save_protocol)
        self.LOAD = QtWidgets.QPushButton("LOAD")
        self.LOAD.clicked.connect(self.load_protocol)
        self.CLEAR = QtWidgets.QPushButton("CLEAR")
        self.CLEAR.clicked.connect(self.clear_protocol)
        self.buttons_container = QtWidgets.QWidget()
        self.buttons_container.setLayout(QtWidgets.QHBoxLayout())
        self.buttons_container.layout().addWidget(self.SAVE)
        self.buttons_container.layout().addWidget(self.LOAD)
        self.buttons_container.layout().addWidget(self.CLEAR)
        self.layout().addWidget(self.buttons_container)

    @staticmethod
    def divider():
        divider = QtWidgets.QFrame()
        divider.setFrameStyle(divider.HLine | divider.Plain)
        divider.setLineWidth(1)
        return divider

    @property
    def n_reps(self):
        return self.reps_spinbox.value()

    @property
    def interval(self):
        """The inter-rep interval in seconds"""
        return self.interval_widget.value / 1000

    def to_protocol(self):
        event_list = self.builder_widget.to_protocol()
        protocol = list(event_list)
        t = self.interval
        for i in range(self.n_reps - 1):
            protocol.append(events.PAUSE(t))
            protocol.extend(list(event_list))
        return protocol

    @property
    def last_directory(self):
        if hasattr(self, "_last_directory"):
            return self._last_directory
        return self.directory

    @last_directory.setter
    def last_directory(self, directory):
        self._last_directory = directory

    @QtCore.pyqtSlot()
    def save_protocol(self):
        event_list = self.builder_widget.to_protocol()
        event_list = [repr(event) for event in event_list]
        t = self.interval_widget.spinbox_value
        unit = self.interval_widget.current_unit
        n_reps = self.n_reps
        now = datetime.now()
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save protocol', self.last_directory, "json files (*.json)")
        path = str(path)
        if path:
            with open(path, "w") as p:
                json.dump(
                    {
                        "event_list": event_list,
                        "repetitions": (n_reps, t, unit),
                        "created": now.strftime("%Y/%m/%d %H:%M:%S")
                    }, p)
            self.last_directory = os.path.dirname(path)

    @QtCore.pyqtSlot()
    def load_protocol(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open protocol', self.last_directory, "json files (*.json)")
        if path:
            with open(path, "rb") as p:
                protocol = json.load(p)
            name = os.path.basename(path)
            name = os.path.splitext(name)[0]
            metadata = protocol["created"]
            print(f"Opening protocol '{name}' from {metadata}")
            n_reps, t, unit = protocol["repetitions"]
            event_list = protocol["event_list"]
            try:
                event_list = [self.str_to_event(event) for event in event_list]
                self.set_protocol(event_list, n_reps, t, unit)
            except ValueError as v:
                print(v)

    @QtCore.pyqtSlot()
    def clear_protocol(self):
        for w in reversed(self.builder_widget.event_widgets):
            w.select()
            self.builder_widget.removeEvent()

    @staticmethod
    def str_to_event(s) -> tuple:
        args = s[6:-1]  # get arguments between parentheses
        if s.startswith("PAUSE"):
            time = re.search("(?<=time=)(.*)", args).group(0)  # find time with regular expression
            time = literal_eval(time)  # convert to float
            return "wait", time
        if s.startswith("EVENT"):
            name = re.search("(?<=name=)'(.*?)'", args).group(1)  # find event name with regular expression
            kw = re.search("(?<=kw=){(.*?)}", args).group(0)  # find kwargs with regular expression
            kw = literal_eval(kw)  # convert to dict
            kw = dict([(k, str(val)) for k, val in kw.items()])  # convert values to strings
            return "event", name, kw
        raise ValueError(f"{s} is not a valid event. Cannot open protocol.")

    @staticmethod
    def convert_time(t):
        if isinstance(t, float):
            return int(t * 1000), "ms"
        if not t % 60:
            return t, "s"
        return t, "min"

    def set_protocol(self, event_list: list, reps: int, time: int, time_unit: str):
        self.clear_protocol()
        self.reps_spinbox.setValue(reps)
        self.interval_widget.setValue(time)
        self.interval_widget.change_unit(time_unit)
        for event in event_list:
            widget = self.builder_widget.addEvent()  # add an event to the builder widget
            event_type, *args = event
            if event_type == "wait":
                widget.dropdown.setCurrentIndex(0)  # set current widget to WaitWidget
                time, = args
                t, unit = self.convert_time(time)
                widget.current_widget.setValue(t)
                widget.current_widget.change_unit(unit)
            if event_type == "event":
                widget.dropdown.setCurrentIndex(1)  # set current widget to EventPicker
                name, kw = args
                widget.current_widget.combo_box.setCurrentText(name)
                try:
                    target = kw.pop("target")
                except KeyError:
                    target = ""
                widget.current_widget.advanced_options["target"] = target
                widget.current_widget.advanced_options["kwargs"] = kw
        self.changed()


class TimedTab(ChangesProtocol, Stateful, QtWidgets.QWidget):
    """Tab for having a simple timed or free-running recording without a protocol."""

    def __init__(self):
        super().__init__()
        self.setLayout(QtWidgets.QGridLayout())
        self.layout().setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        # Checkbox
        self.freerun_checkbox = QtWidgets.QCheckBox("Free-running")
        self.freerun_checkbox.stateChanged.connect(self.change_freerun)
        # Label
        self.duration_label = QtWidgets.QLabel("Duration:")
        # Time
        self.duration_widget = TimeUnitWidget()
        self.duration_widget.addSeconds(minval=1)
        self.duration_widget.addMinutes(minval=1)
        self.duration_widget.valueChanged.connect(self.changed)
        # Add to layout
        self.layout().addWidget(self.freerun_checkbox, 0, 0, 1, 2)
        self.layout().addWidget(self.duration_label, 1, 0, 1, 1)
        self.layout().addWidget(self.duration_widget, 1, 1, 1, 1)

    @QtCore.pyqtSlot(int)
    def change_freerun(self, state):
        if state:  # checked
            self.duration_label.setVisible(False)
            self.duration_widget.setVisible(False)
        else:  # not checked
            self.duration_label.setVisible(True)
            self.duration_widget.setVisible(True)
        self.changed()

    def to_protocol(self):
        if self.freerun_checkbox.checkState():
            return [events.FREERUN()]
        return [events.PAUSE(self.duration_widget.value / 1000)]


class TrialStructureWidget(ChangesProtocol, Stateful, QtWidgets.QGroupBox):
    """Top-level widget that is displayed in the experiment control dock.

    Parameters
    ----------
    triggers : tuple
        Not currently implemented, but could be used to trigger the start and end of a recording.
    event_names : tuple of str
        Names of gui_events from Pydra workers.
    targets : tuple of str
        Names of workers in Pydra network.
    """

    protocol_changed = QtCore.pyqtSignal(list)  # top-level signal emitted whenever another widget changes the protocol

    def __init__(self, triggers=(), event_names=(), targets=(), **kwargs):
        super().__init__("Trial structure")
        self.triggers = triggers
        self.event_names = event_names
        self.targets = targets
        # Layout
        self.setLayout(QtWidgets.QGridLayout())
        self.layout().setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        # -----
        # START
        # -----
        # Start label
        self.start_label = QtWidgets.QLabel("START RECORDING")
        self.start_label.setFrameShape(QtWidgets.QFrame.Panel)
        self.start_label.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.start_label.setLineWidth(2)
        # Start trigger
        self.start_trigger_check = QtWidgets.QCheckBox("triggered")
        self.start_trigger_dropdown = QtWidgets.QComboBox()
        self.start_trigger_dropdown.addItems(self.triggers)
        self.start_trigger_dropdown.setEnabled(False)
        # Add to layout
        self.layout().addWidget(self.start_label, 0, 0)
        self.layout().addWidget(self.start_trigger_check, 0, 1)
        self.layout().addWidget(self.start_trigger_dropdown, 0, 2)
        # --------
        # PROTOCOL
        # --------
        self.timed_widget = TimedTab()
        self.protocol_widget = ProtocolTab(self.event_names, self.targets)
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.addTab(self.timed_widget, "Timed")
        self.tab_widget.addTab(self.protocol_widget, "Protocol")
        self.layout().addWidget(self.tab_widget, 1, 0, 1, 3)
        self.tab_widget.currentChanged.connect(self.changed)
        # ----
        # STOP
        # ----
        # Stop label
        self.stop_label = QtWidgets.QLabel("STOP RECORDING")
        self.stop_label.setFrameShape(QtWidgets.QFrame.Panel)
        self.stop_label.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.stop_label.setLineWidth(2)
        # Stop trigger
        self.stop_trigger_check = QtWidgets.QCheckBox("triggered")
        self.stop_trigger_dropdown = QtWidgets.QComboBox()
        self.stop_trigger_dropdown.addItems(self.triggers)
        self.stop_trigger_dropdown.setEnabled(False)
        # Add to layout
        self.layout().addWidget(self.stop_label, 2, 0)
        self.layout().addWidget(self.stop_trigger_check, 2, 1)
        self.layout().addWidget(self.stop_trigger_dropdown, 2, 2)
        # --------------------------
        # Catch all protocol changes
        # --------------------------
        self.protocol_changed.connect(self.stateMachine.set_protocol)
        self._protocol_change_proxy.connect(self.update_protocol)

    @property
    def protocol_list(self) -> list:
        return self.tab_widget.currentWidget().to_protocol()

    @QtCore.pyqtSlot()
    def update_protocol(self):
        self.protocol_changed.emit(self.protocol_list)

    def enterIdle(self):
        self.setEnabled(True)

    def enterRunning(self):
        self.setEnabled(False)
