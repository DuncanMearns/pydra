from ..core import SavingWorker, Plugin
from ..gui import PluginWidget
import cv2
from PyQt5 import QtCore, QtWidgets
from pathlib import Path
import json
import numpy as np


class VideoTrackingSavingWorker(SavingWorker):

    def __init__(self, video_path, fourcc: str, frame_rate: float, frame_size: tuple, saving_on=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.video_path = video_path
        self.fourcc = fourcc
        self.frame_rate = frame_rate
        self.frame_size = frame_size
        self.saving_on = saving_on

    def setup(self):
        super().setup()
        if self.saving_on:
            self.metadata['time'] = []
            path = Path(self.video_path)
            self.metadata_path = path.parent.joinpath(path.stem + '.json')
            self.points = []
            self.points_path = path.parent.joinpath(path.stem + '_points' + '.npy')
            self.angles = []
            self.angles_path = path.parent.joinpath(path.stem + '_angles' + '.npy')
            try:
                assert self.video_path is not None
                fourcc = cv2.VideoWriter_fourcc(*self.fourcc)
                self.writer = cv2.VideoWriter(self.video_path, fourcc, self.frame_rate, self.frame_size, False)
            except Exception:
                print('SAVING NOT INITIALIZED CORRECTLY!')
        return

    def save_to_metadata(self, timestamp, data):
        if self.saving_on:
            try:
                self.metadata['optogenetics'].append([timestamp, data])
            except KeyError:
                self.metadata['optogenetics'] = [[timestamp, data]]

    def dump(self, frame_number, timestamp, frame, tracking):
        if self.saving_on:
            try:
                self.writer.encode(frame)
                self.metadata['time'].append([frame_number, timestamp])
                try:
                    self.points.append(tracking['points'])
                    self.angles.append(tracking['angle'])
                except KeyError:
                    pass
                # for key, val in tracking.items():
                #     try:
                #         self.metadata[key].append(val)
                #     except KeyError:
                #         self.metadata[key] = [val]
            except AttributeError:
                pass
        return

    def cleanup(self):
        super().cleanup()
        if self.saving_on:
            try:
                self.writer.release()
            except AttributeError:
                pass
            with open(self.metadata_path, 'w') as path:
                json.dump(self.metadata, path)
            points = np.array(self.points)
            np.save(self.points_path, points)
            angles = np.array(self.angles)
            np.save(self.angles_path, angles)
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

    def idle(self):
        self.setEnabled(True)

    def live(self):
        self.setEnabled(False)

    def record(self):
        self.setEnabled(False)


class VideoTrackingSaver(Plugin):

    name = 'VideoSaver'
    worker = VideoTrackingSavingWorker
    params = {'video_path': None,
              'fourcc': 'XVID',
              'frame_rate': None,
              'frame_size': None,
              'saving_on': False}
    widget = SavingWidget

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

    @QtCore.pyqtSlot(str, dict)
    def update_recording_params(self, target, new_vals):
        if 'frame_rate' in new_vals:
            self.params['frame_rate'] = new_vals['frame_rate']
        if 'frame_size' in new_vals:
            self.params['frame_size'] = new_vals['frame_size']
        self.paramsChanged.emit(self.name, dict(frame_rate=self.params['frame_rate'],
                                                frame_size=self.params['frame_size']))
