from PyQt5 import QtWidgets, QtCore, QtGui

from ..layout import *
from ..dynamic import Stateful


class FileNamingWidget(Stateful, QtWidgets.QGroupBox):

    minWidth = 150

    directory_changed = QtCore.pyqtSignal(str)
    filename_changed = QtCore.pyqtSignal(str)

    def __init__(self, directory, filename, *, n_trial_digits=3):
        super().__init__("File naming")
        # Layout
        self.setLayout(QtWidgets.QGridLayout())
        self.layout().setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        # -----------------
        # Working directory
        # -----------------
        self.directory = str(directory)
        # Label
        self.directory_label = QtWidgets.QLabel("Working directory")
        # Editor
        self.directory_editor = QtWidgets.QLineEdit(self.directory)
        self.directory_editor.setReadOnly(True)
        self.directory_editor.setMinimumSize(self.minWidth, LINEEDIT_HEIGHT)
        self.directory_editor.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        self.directory_changed.connect(self.directory_editor.setText)
        self.directory_changed.connect(self.update_size)
        # Button
        self.directory_button = QtWidgets.QPushButton("change")
        self.directory_button.clicked.connect(self.change_directory)
        # Add to layout
        self.layout().addWidget(self.directory_label, 0, 0, alignment=QtCore.Qt.AlignLeft)
        self.layout().addWidget(self.directory_editor, 1, 0, alignment=QtCore.Qt.AlignLeft)
        self.layout().addWidget(self.directory_button, 1, 1, alignment=QtCore.Qt.AlignLeft)
        # -----------
        # File naming
        # -----------
        self.filename = str(filename)
        # Label
        self.filename_label = QtWidgets.QLabel("File basename")
        # Editor
        self.filename_editor = QtWidgets.QLineEdit()
        self.filename_editor.setPlaceholderText('Enter file name')
        self.filename_editor.setMinimumSize(self.minWidth, LINEEDIT_HEIGHT)
        self.filename_editor.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        self.filename_editor.textChanged.connect(self.update_size)
        self.filename_editor.editingFinished.connect(self.change_filename)
        # Trial number
        self.trial_label = QtWidgets.QLineEdit()
        # Extension
        self.filename_ext_label = QtWidgets.QLabel(".ext")
        # Add to layout
        self.layout().addWidget(self.filename_label, 2, 0, alignment=QtCore.Qt.AlignLeft)
        self.layout().addWidget(self.filename_editor, 3, 0, alignment=QtCore.Qt.AlignLeft)
        self.layout().addWidget(self.filename_ext_label, 3, 1, alignment=QtCore.Qt.AlignLeft)

    @QtCore.pyqtSlot()
    def change_directory(self):
        """Opens a dialog to changes the current working directory."""
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select directory', self.directory)
        directory = str(directory)
        if directory != '':
            self.directory = directory
            self.directory_changed.emit(directory)

    @QtCore.pyqtSlot(str)
    def update_size(self, text):
        """Updates line editor sizes to fit text."""
        fm = QtGui.QFontMetrics(QtGui.QFont())
        wd = self.directory_editor.text() + "  "
        fn = self.filename_editor.text() + "  "
        w1 = fm.horizontalAdvance(wd)
        w2 = fm.horizontalAdvance(fn)
        w = max([self.minWidth, w1, w2])
        self.directory_editor.setMinimumSize(QtCore.QSize(w, LINEEDIT_HEIGHT))
        self.filename_editor.setMinimumSize(QtCore.QSize(w, LINEEDIT_HEIGHT))

    def change_filename(self):
        # TODO: check overwrite
        print(self.filename)
        self.filename_changed.emit(self.filename)

    def enterRunning(self):
        self.setEnabled(False)

    def enterIdle(self):
        self.setEnabled(True)
