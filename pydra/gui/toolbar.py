from PyQt5 import QtWidgets, QtCore
from .states import StateEnabled
from pathlib import Path


BUTTON_WIDTH = 100
BUTTON_HEIGHT = 50


class RecordButton(QtWidgets.QPushButton, StateEnabled):

    def __init__(self, *args, **kwargs):
        super().__init__("RECORD", *args, **kwargs)
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPlay')))
        self.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)

    def setIdle(self):
        self.setEnabled(True)
        self.setText("RECORD")
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPlay')))

    def setRecord(self):
        self.setText("STOP")
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaStop')))


class DirectoryWidget(QtWidgets.QGroupBox, StateEnabled):

    changed = QtCore.pyqtSignal(str)

    def __init__(self, directory, *args, **kwargs):
        super().__init__("Working directory", *args, **kwargs)
        # Directory
        self.directory = str(directory)
        # Layout
        self.setLayout(QtWidgets.QHBoxLayout())
        # Change directory button
        self.button = QtWidgets.QPushButton("change")
        self.button.clicked.connect(self.change_directory)
        self.layout().addWidget(self.button)
        # Directory label
        self.directory_label = QtWidgets.QLabel(self.directory)
        self.layout().addWidget(self.directory_label, alignment=QtCore.Qt.AlignLeft)

    def change_directory(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select directory', self.directory)
        directory = str(directory)
        if directory != '':
            self.directory = directory
            self.directory_label.setText(self.directory)
            self.changed.emit(directory)

    def setRecord(self):
        self.button.setEnabled(False)

    def setIdle(self):
        self.button.setEnabled(True)


class FileNamingWidget(QtWidgets.QGroupBox, StateEnabled):

    changed = QtCore.pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super().__init__("File naming", *args, **kwargs)
        # Layout
        self.setLayout(QtWidgets.QHBoxLayout())
        # Basename editor
        self.editor = QtWidgets.QLineEdit()
        self.editor.setPlaceholderText('Enter file name')
        self.editor.editingFinished.connect(self.change_basename)
        self.layout().addWidget(QtWidgets.QLabel("Basename:"), alignment=QtCore.Qt.AlignLeft)
        self.layout().addWidget(self.editor, alignment=QtCore.Qt.AlignLeft)
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

    def setRecord(self):
        self.editor.setEnabled(False)
        self.autonaming.setEnabled(False)
        self.spinbox.setEnabled(False)

    def endRecord(self):
        if self.autonaming_enabled:
            self.spinbox.setValue(self.spinbox.value() + 1)

    def setIdle(self):
        self.editor.setEnabled(True)
        self.autonaming.setEnabled(True)
        self.spinbox.setEnabled(True)


def checked(method):
    def check_naming_conflict(toolbar, val):
        directory = Path(toolbar.directory_widget.directory)
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


class RecordingToolbar(QtWidgets.QToolBar, StateEnabled):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        # Set params
        self.setFloatable(False)
        self.setMovable(False)
        # Record button
        self.record_button = RecordButton()
        self.addWidget(self.record_button)
        self.addSeparator()
        # Directory widget
        self.directory_widget = DirectoryWidget(self.parent().pydra.working_dir)
        self.addWidget(self.directory_widget)
        self.addSeparator()
        # File naming widget
        self.filename_widget = FileNamingWidget()
        self.addWidget(self.filename_widget)
        # State transitions
        self.parent().idleState.addTransition(self.record_button.clicked, self.parent().recordState)
        self.parent().recordState.addTransition(self.record_button.clicked, self.parent().idleState)
        # Signals
        self.directory_widget.changed.connect(self.set_working_directory)
        self.filename_widget.changed.connect(self.set_filename)

    @checked
    def set_filename(self, filename):
        self.parent().pydra.set_filename(filename)

    @checked
    def set_working_directory(self, directory):
        self.parent().pydra.set_working_directory(directory)
