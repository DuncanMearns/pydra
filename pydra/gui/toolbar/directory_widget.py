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
