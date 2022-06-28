from pydra.gui.dynamic import Stateful
from PyQt5 import QtWidgets, QtCore
from pathlib import Path


class RecordingToolbar(Stateful, QtWidgets.QToolBar):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        # Set params
        self.setFloatable(False)
        self.setMovable(False)
        # Record button
        self.record_button = RecordButton()
        self.stateMachine.idle.addTransition(self.record_button.clicked, self.stateMachine.running)
        self.stateMachine.running.addTransition(self.record_button.clicked, self.stateMachine.idle)
        self.addWidget(self.record_button)
        self.addSeparator()
        # # Directory widget
        # self.directory_widget = DirectoryWidget(self.parent().pydra.working_dir)
        # self.addWidget(self.directory_widget)
        # self.addSeparator()
        # # File naming widget
        # self.filename_widget = FileNamingWidget()
        # self.addWidget(self.filename_widget)
        # self.addSeparator()
        # # Protocol widget
        # self.protocol_widget = ProtocolWidget()
        # self.protocol_widget.editor_clicked.connect(self.show_protocol)
        # self.addWidget(self.protocol_widget)
        # # Signals
        # self.directory_widget.changed.connect(self.set_working_directory)
        # self.filename_widget.changed.connect(self.set_filename)

    # @checked
    def set_filename(self, filename):
        self.parent().pydra.set_filename(filename)

    # @checked
    def set_working_directory(self, directory):
        self.parent().pydra.set_working_directory(directory)

    def show_protocol(self):
        self.parent().protocol_window.show()



class FileWidget(Stateful, QtWidgets.QGroupBox):

    changed = QtCore.pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super().__init__("File naming", *args, **kwargs)
        # Layout
        self.setLayout(QtWidgets.QHBoxLayout())
        # Autonaming
        self.autonaming = QtWidgets.QCheckBox("Increment #")
        self.autonaming.setChecked(True)
        self.autonaming.stateChanged.connect(self.toggle_autonaming)
        self.spinbox = QtWidgets.QSpinBox()
        self.spinbox.setRange(1, 999)
        self.spinbox.valueChanged.connect(self.update_filename)
        self.layout().addWidget(self.autonaming)
        self.layout().addWidget(self.spinbox)
        # Filename
        self.layout().addWidget(QtWidgets.QLabel("File name:"))
        self.filename_label = QtWidgets.QLabel(self.filename + ".ext")
        self.layout().addWidget(self.filename_label)

    @property
    def editor_text(self):
        return str(self.editor.text())

    @property
    def autonaming_enabled(self):
        return self.autonaming.isChecked()

    def toggle_autonaming(self, state):
        if state:
            self.spinbox.setEnabled(True)
        else:
            self.spinbox.setEnabled(False)
        self.update_filename()

    @property
    def filename(self):
        name = self.editor_text
        if name:
            if self.autonaming_enabled:
                digits = str(self.spinbox.value())
                digits = "".join((["0"] * (3 - len(digits))) + [digits])
                name = "_".join([name, digits])
        return name

    def change_basename(self):
        if self.autonaming_enabled:
            self.spinbox.setValue(1)
        self.update_filename()

    def update_filename(self):
        self.filename_label.setText(self.filename + ".ext")
        self.changed.emit(self.filename)

    def enterRunning(self):
        self.editor.setEnabled(False)
        self.autonaming.setEnabled(False)
        self.spinbox.setEnabled(False)

    def stopRecord(self):
        if self.autonaming_enabled:
            self.spinbox.setValue(self.spinbox.value() + 1)

    def enterIdle(self):
        self.editor.setEnabled(True)
        self.autonaming.setEnabled(True)
        if self.autonaming_enabled:
            self.spinbox.setEnabled(True)


def checked(method):
    def check_naming_conflict(toolbar, val):
        directory = Path(toolbar.filenaming_group.directory)
        filename = toolbar.filename_widget.filename
        if filename:
            conflicts = list(directory.glob(f"{filename}*"))
            if len(conflicts):
                paths = "\n".join([str(conflict) for conflict in conflicts])
                dialog = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
                                               "Warning",
                                               f"File already exists!\n\n{paths}",
                                               parent=toolbar)
                dialog.show()
        return method(toolbar, val)
    return check_naming_conflict

