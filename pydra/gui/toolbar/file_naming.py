from PyQt5 import QtWidgets, QtCore
from ..states import StateEnabled


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

    def enterRunning(self):
        self.button.setEnabled(False)

    def enterIdle(self):
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

    def enterRunning(self):
        self.editor.setEnabled(False)
        self.autonaming.setEnabled(False)
        self.spinbox.setEnabled(False)

    def endRecord(self, i):
        if self.autonaming_enabled:
            self.spinbox.setValue(self.spinbox.value() + 1)

    def enterIdle(self):
        self.editor.setEnabled(True)
        self.autonaming.setEnabled(True)
        if self.autonaming_enabled:
            self.spinbox.setEnabled(True)
