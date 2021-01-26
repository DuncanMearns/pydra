from PyQt5 import QtWidgets, QtCore
from .states import StateEnabled
from .display import *


class EventWidget(QtWidgets.QWidget):

    def __init__(self, events, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = events
        self.setLayout(QtWidgets.QHBoxLayout())
        self.combo_box = QtWidgets.QComboBox()
        self.combo_box.addItems([event[0] for event in self.events])
        self.combo_box.currentIndexChanged.connect(self.selectionChanged)
        self.layout().addWidget(self.combo_box)
        self.workers_label = QtWidgets.QLabel("")
        self.layout().addWidget(self.workers_label)
        self.combo_box.setCurrentIndex(0)
        self.selectionChanged(0)

    def selectionChanged(self, i):
        text = ", ".join(self.events[i][1])
        self.workers_label.setText(text)

    @property
    def value(self):
        return self.events[self.combo_box.currentIndex()][0]


class TimerWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.spinbox = QtWidgets.QSpinBox()
        self.layout().addWidget(self.spinbox)
        self.layout().addWidget(QtWidgets.QLabel("seconds"))

    @property
    def value(self):
        return self.spinbox.value()


class ProtocolWidget(QtWidgets.QGroupBox):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTitle("Protocol")
        self.setLayout(QtWidgets.QGridLayout())
        # List of widgets
        self.widgets = []
        # Start recording
        self.start_recording = QtWidgets.QPushButton("start_recording")
        self.start_recording.setEnabled(False)
        # Buttons
        self.buttons = QtWidgets.QWidget()
        self.buttons.setLayout(QtWidgets.QHBoxLayout())
        self.timer_button = QtWidgets.QPushButton("+ timer")
        self.timer_button.clicked.connect(self.add_timer)
        self.event_button = QtWidgets.QPushButton("+ event")
        self.event_button.clicked.connect(self.add_event)
        for button in (self.timer_button, self.event_button):
            self.buttons.layout().addWidget(button)
        # Stop recording
        self.stop_recording = QtWidgets.QPushButton("stop_recording")
        self.stop_recording.setEnabled(False)
        # Update UI
        self.updateUI()

    def updateUI(self):
        # Clear widgets
        for i in reversed(range(self.layout().count())):
            self.layout().itemAt(i).widget().setParent(None)
        # Add new widgets
        self.layout().addWidget(self.start_recording, 0, 0, 1, 3)
        self.layout().addWidget(self.separator(), 1, 0, 1, 3)
        i = 2
        self.remove_buttons = QtWidgets.QButtonGroup()
        self.remove_buttons.buttonClicked.connect(self.remove)
        for widget in self.widgets:
            self.layout().addWidget(widget, i, 0, 1, 2)
            remove_button = QtWidgets.QPushButton("remove")
            self.remove_buttons.addButton(remove_button, (i // 2) - 1)
            self.layout().addWidget(remove_button, i, 2, 1, 1)
            self.layout().addWidget(self.separator(), i + 1, 0, 1, 3)
            i += 2
        self.layout().addWidget(self.stop_recording, i, 0, 1, 3)
        self.layout().addWidget(self.buttons, i + 1, 0, 1, 2)

    @staticmethod
    def separator():
        line = QtWidgets.QFrame()
        line.setFrameStyle(line.HLine | line.Plain)
        return line

    def remove(self, row):
        idx = self.remove_buttons.id(row)
        self.widgets.pop(idx)
        self.updateUI()

    def add_event(self):
        self.widgets.append(EventWidget(self.parent().events))
        self.updateUI()

    def add_timer(self):
        self.widgets.append(TimerWidget())
        self.updateUI()

    def clear(self):
        self.widgets = []
        self.updateUI()

    @property
    def protocol(self):
        return [widget.value for widget in self.widgets]


class ProtocolBuilder(QtWidgets.QWidget):

    save_protocol = QtCore.pyqtSignal(str, list)

    default_events = ("start_recording", "stop_recording")

    def __init__(self, events, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = [event for event in events.items() if event[0] not in self.default_events]
        self.setWindowTitle("Protocol builder")
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setAlignment(QtCore.Qt.AlignTop)
        # BUTTONS
        self.buttons_widget = QtWidgets.QWidget()
        self.buttons_widget.setLayout(QtWidgets.QHBoxLayout())
        self.new_button = QtWidgets.QPushButton("NEW")
        self.new_button.clicked.connect(self.newProtocol)
        self.load_button = QtWidgets.QPushButton("LOAD")
        self.load_button.clicked.connect(self.loadProtocol)
        self.save_button = QtWidgets.QPushButton("SAVE")
        self.save_button.clicked.connect(self.saveProtocol)
        for button in (self.new_button, self.load_button, self.save_button):
            button.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            self.buttons_widget.layout().addWidget(button)
        self.layout().addWidget(self.buttons_widget, alignment=QtCore.Qt.AlignTop)
        # PROTOCOL NAME
        self.name_widget = QtWidgets.QWidget()
        self.name_widget.setLayout(QtWidgets.QFormLayout())
        self.name_editor = QtWidgets.QLineEdit()
        self.name_widget.layout().addRow("Name:", self.name_editor)
        self.layout().addWidget(self.name_widget, alignment=QtCore.Qt.AlignTop)
        # PROTOCOL
        self.protocol_widget = ProtocolWidget(parent=self)
        self.layout().addWidget(self.protocol_widget, alignment=QtCore.Qt.AlignTop)

    @property
    def name(self) -> str:
        return self.name_editor.text()

    @property
    def protocol(self) -> list:
        return self.protocol_widget.protocol

    def saveProtocol(self):
        self.save_protocol.emit(self.name, self.protocol)

    def loadProtocol(self):
        return

    def newProtocol(self):
        self.name_editor.setText("")
        self.protocol_widget.clear()


class RunButton(QtWidgets.QPushButton, StateEnabled):

    def __init__(self, *args, **kwargs):
        super().__init__("RUN", *args, **kwargs)
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPlay')))
        self.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)

    def enterProtocol(self):
        self.setEnabled(True)
        self.setText("RUN")
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPlay')))

    def exitProtocol(self):
        self.setText("STOP")
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaStop')))


class SpinboxWidget(QtWidgets.QWidget):

    def __init__(self, label, minVal=0, suffix: str=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLayout(QtWidgets.QFormLayout())
        self.spinbox = QtWidgets.QSpinBox()
        self.spinbox.setMinimum(minVal)
        if suffix is not None:
            self.spinbox.setSuffix(f" {suffix}")
        self.layout().addRow(f"{label}: ", self.spinbox)

    @property
    def value(self):
        return self.spinbox.value()


class RepetitionsWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLayout(QtWidgets.QHBoxLayout())
        # N repetitions
        self.repetitions_widget = SpinboxWidget("Repetitions", minVal=1)
        self.layout().addWidget(self.repetitions_widget)
        # Interval
        self.interval_widget = SpinboxWidget("Interval", suffix="s")
        self.layout().addWidget(self.interval_widget)


class ProtocolToolbar(QtWidgets.QToolBar, StateEnabled):

    clicked = QtCore.pyqtSignal()

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        # Protocol builder button
        self.builder_button = QtWidgets.QPushButton("Protocol...")
        self.builder_button.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
        self.builder_button.clicked.connect(self.show_builder)
        self.addWidget(self.builder_button)
        # Run button
        self.run_button = RunButton()
        self.run_button.clicked.connect(self.clickRun)
        self.addWidget(self.run_button)
        # Repetitions widget
        self.repetitions = RepetitionsWidget()
        self.addWidget(self.repetitions)

    def show_builder(self):
        self.parent().protocol_builder.show()

    def clickRun(self):
        self.clicked.emit()
