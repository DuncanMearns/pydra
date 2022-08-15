from PyQt5 import QtWidgets, QtCore, QtGui
import os

from ..layout import *
from ..dynamic import Stateful


class SpinBoxLeadingZeros(QtWidgets.QSpinBox):

    def __init__(self, n):
        super().__init__()
        self.n = n
        self.setMaximum(self.max)

    @property
    def max(self):
        return int("9" * self.n)

    def textFromValue(self, v: int) -> str:
        text = str(v)
        while len(text) < self.n:
            text = "0" + text
        return text


class FileNamingWidget(Stateful, QtWidgets.QGroupBox):

    minWidth = 150

    directory_changed = QtCore.pyqtSignal(str)
    filename_changed = QtCore.pyqtSignal(str)
    trial_number_changed = QtCore.pyqtSignal(int)

    def __init__(self, directory, filename, n_trial_digits=3):
        super().__init__("File naming")
        # Layout
        self.setLayout(QtWidgets.QGridLayout())
        self.layout().setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        # -----------------
        # Working directory
        # -----------------
        # Label
        self.directory_label = QtWidgets.QLabel("Working directory")
        # Editor
        self.directory_editor = QtWidgets.QLineEdit(directory)
        self.directory_editor.setReadOnly(True)
        self.directory_editor.setMinimumSize(self.minWidth, LINEEDIT_HEIGHT)
        self.directory_editor.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        self.directory_changed.connect(self.directory_editor.setText)
        self.directory_changed.connect(self.update_size)
        self.directory_changed.connect(self.stateMachine.set_directory)
        # Button
        self.directory_button = QtWidgets.QPushButton("change")
        self.directory_button.clicked.connect(self.change_directory)
        # Add to layout
        self.layout().addWidget(self.directory_label, 0, 0)
        self.layout().addWidget(self.directory_editor, 1, 0)
        self.layout().addWidget(self.directory_button, 1, 1)
        # -----------
        # File naming
        # -----------
        # Label
        self.filename_label = QtWidgets.QLabel("File basename")
        # Editor
        self.filename_editor = QtWidgets.QLineEdit()
        self.filename_editor.setText(filename)
        self.filename_editor.setPlaceholderText('Enter file name')
        self.filename_editor.setMinimumSize(self.minWidth, LINEEDIT_HEIGHT)
        self.filename_editor.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        self.filename_editor.textChanged.connect(self.update_size)
        self.filename_editor.editingFinished.connect(self.change_filename)
        self.filename_changed.connect(self.stateMachine.set_filename)
        # Trial number
        self.trial_number_editor = SpinBoxLeadingZeros(n_trial_digits)
        self.trial_number_editor.setMinimum(1)
        self.trial_number_editor.valueChanged.connect(self.change_trial_number)
        self.trial_number_widget = QtWidgets.QWidget()
        self.trial_number_widget.setLayout(QtWidgets.QHBoxLayout())
        self.trial_number_widget.layout().setAlignment(QtCore.Qt.AlignLeft)
        self.trial_number_widget.layout().addWidget(QtWidgets.QLabel("_"))
        self.trial_number_widget.layout().addWidget(self.trial_number_editor)
        self.trial_number_widget.layout().addWidget(QtWidgets.QLabel(".ext"))
        self.trial_number_changed.connect(self.stateMachine.set_trial_number)
        # Add to layout
        self.layout().addWidget(self.filename_label, 2, 0)
        self.layout().addWidget(self.filename_editor, 3, 0)
        self.layout().addWidget(self.trial_number_widget, 3, 1)

    @property
    def filename_text(self):
        return self.filename_editor.text() + "_" + self.trial_number_editor.text()

    @property
    def directory_text(self):
        return self.directory_editor.text()

    @property
    def trial_number_text(self):
        return self.trial_number_editor.value()

    @QtCore.pyqtSlot()
    def change_directory(self):
        """Opens a dialog to changes the current working directory."""
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select directory', self.directory_text)
        directory = str(directory)
        if directory != '':
            self.check_validity()
            self.directory_changed.emit(directory)

    @QtCore.pyqtSlot()
    def change_filename(self):
        self.check_validity()
        self.filename_changed.emit(self.filename_text)

    @QtCore.pyqtSlot(int)
    def change_trial_number(self, i):
        self.trial_number_changed.emit(i)
        self.change_filename()

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

    @property
    def existing_files(self):
        if os.path.exists(self.directory):
            directory = self.directory
        else:
            directory = os.getcwd()
        return [os.path.splitext(f)[0] for f in os.listdir(directory)]

    def check_validity(self):
        if self.filename_text in self.existing_files:
            dialog = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
                                           "Warning",
                                           f"File already exists!\n\n{self.filename}",
                                           parent=self)
            dialog.show()

    def enterRunning(self):
        self.setEnabled(False)

    def enterIdle(self):
        self.setEnabled(True)

    def stopRecord(self):
        self.trial_number_editor.setValue(self.trial_number + 1)
