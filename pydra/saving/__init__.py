from ..core import SavingWorker, Plugin
from ..gui.widget import PluginWidget
import cv2
from PyQt5 import QtCore, QtWidgets
from pathlib import Path


class NoSaver(SavingWorker):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class VideoSavingWorker(SavingWorker):

    def __init__(self, video_path, fourcc: str, frame_rate: float, frame_size: tuple, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.video_path = video_path
        self.fourcc = fourcc
        self.frame_rate = frame_rate
        self.frame_size = frame_size

    def setup(self):
        fourcc = cv2.VideoWriter_fourcc(*self.fourcc)
        self.writer = cv2.VideoWriter(self.video_path, fourcc, self.frame_rate, self.frame_size, False)
        return

    def dump(self, frame_number, timestamp, frame, tracking):
        print(frame_number)
        self.writer.write(frame)
        return

    def cleanup(self):
        self.writer.release()
        return


class SavingWidget(PluginWidget):

    def __init__(self, plugin, *args, **kwargs):
        super().__init__(plugin, *args, **kwargs)
        # Name
        self.setWindowTitle('Saving')
        # Working folder
        self.directory_label = QtWidgets.QLabel(self.directory_text)
        self.change_directory_button = QtWidgets.QPushButton('change')
        self.change_directory_button.clicked.connect(self.change_working_directory)
        self.widget().layout().addWidget(QtWidgets.QLabel('Working directory:'), 0, 0, alignment=QtCore.Qt.AlignLeft)
        self.widget().layout().addWidget(self.directory_label, 0, 1, alignment=QtCore.Qt.AlignLeft)
        self.widget().layout().addWidget(self.change_directory_button, 0, 2, alignment=QtCore.Qt.AlignLeft)
        # File name
        self.filename_editor = QtWidgets.QLineEdit()
        self.filename_editor.setPlaceholderText('Enter file name')
        self.filename_editor.editingFinished.connect(self.filename_changed)
        self.widget().layout().addWidget(QtWidgets.QLabel('File name:'), 1, 0, alignment=QtCore.Qt.AlignLeft)
        self.widget().layout().addWidget(self.filename_editor, 1, 1, alignment=QtCore.Qt.AlignLeft)
        self.widget().layout().addWidget(QtWidgets.QLabel('.avi'), 1, 2, alignment=QtCore.Qt.AlignLeft)
        # Output
        self.widget().layout().addWidget(QtWidgets.QLabel('Saving to:'), 2, 0, alignment=QtCore.Qt.AlignLeft)
        self.output_label = QtWidgets.QLabel('')
        self.widget().layout().addWidget(self.output_label, 2, 1, alignment=QtCore.Qt.AlignLeft)

    @property
    def directory_text(self):
        return str(self.plugin.working_directory)

    @property
    def filename_text(self):
        return str(self.filename_editor.text())

    def update_output_text(self):
        if self.plugin.params['video_path']:
            self.output_label.setText(str(self.plugin.params['video_path']))
        else:
            self.output_label.setText('')

    @QtCore.pyqtSlot()
    def filename_changed(self):
        self.plugin.change_filename(self.filename_text)
        self.update_output_text()

    def change_working_directory(self):
        """Opens a file dialog to select a new working folder for saving"""
        new_working_directory = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                           'Select directory',
                                                                           str(self.plugin.default_directory))
        new_working_directory = str(new_working_directory)
        if new_working_directory != '':
            self.plugin.change_working_directory(new_working_directory)
            self.directory_label.setText(self.directory_text)
        self.update_output_text()

    def set_editable(self, val: bool):
        self.change_directory_button.setEnabled(val)
        self.filename_editor.setReadOnly(not val)

    def idle(self):
        self.set_editable(True)

    def live(self):
        self.set_editable(False)

    def record(self):
        self.set_editable(False)


class VideoSaver(Plugin):

    name = 'VideoSaver'
    worker = VideoSavingWorker
    widget = SavingWidget

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params['video_path'] = None
        self.params['fourcc'] = 'XVID'
        self.params['frame_rate'] = None
        self.params['frame_size'] = None

        self.default_directory = Path(r'E:\\')
        self.working_directory = self.default_directory
        self.filename = ''

    def change_filename(self, name):
        self.filename = str(name)
        self.update_output_path()

    def change_working_directory(self, path):
        self.working_directory = Path(path)
        self.update_output_path()

    def update_output_path(self):
        if self.filename:
            self.params['video_path'] = str(self.working_directory.joinpath(self.filename + '.avi'))
        else:
            self.params['video_path'] = None
        self.paramsChanged.emit(self.name, (('video_path', self.params['video_path']),))
