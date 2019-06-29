from ..camera import *
from ..camera.cameras.pike import CameraThread
from ..tracking import TrackerThread, Tracker
from ..saving import SaverThread, SaveProgressWindow, VideoSaver
from PyQt5 import QtCore, QtWidgets
import pyqtgraph as pg
import collections
import os
import cv2
import datetime
import numpy as np


class BaseGUI(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(BaseGUI, self).__init__(*args, **kwargs)

        # =========================
        # SETUP TRACKING AND SAVING
        # =========================

        # Tracking object (may be overwritten in subclass)
        self.tracker = Tracker
        self.tracking_kwargs = {}

        # Saving object (may be overwritten in subclass)
        self.saver = VideoSaver
        self.saving_kwargs = {}

        # Create caches for new frames, newly tracked data, and displays
        self._frame_buffer = 5000
        self.frame_cache_input = collections.deque(maxlen=self._frame_buffer)
        self.frame_cache_output = collections.deque(maxlen=self._frame_buffer)
        self.caches = []  # user-defined caches can go in here

        # ============
        # SETUP CAMERA
        # ============

        # Start the cameras thread
        self.frameSize = (340, 240)  # (width, height)
        self.frameRate = 300  # fps
        self._spawn_camera_thread()

        # ==========================
        # SETUP DISPLAY UPDATE TIMER
        # ==========================

        # Create timer for handling display updates
        # This ensures that events sent from recording or tracking threads don't queue up waiting to be processed
        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_plots)
        self.timer.start()

        # =================
        # SETUP MAIN WINDOW
        # =================

        # Layout sizes
        mainWidth = 800
        mainHeight = 600
        buttonWidth = 100
        buttonHeight = 20

        # Setup main window
        self.resize(mainWidth, mainHeight)
        self.w = QtWidgets.QWidget()
        self.setCentralWidget(self.w)
        self.setWindowTitle('Camera')

        self.main_layout = QtWidgets.QVBoxLayout()
        self.w.setLayout(self.main_layout)

        # ----------------------------------------------------------------------------
        # Top row: [LIVE] [RECORD] [WORKING FOLDER] [FILENAME] [CHANGE WORKING FOLDER]
        # ----------------------------------------------------------------------------

        layout_top_row = QtWidgets.QHBoxLayout()
        layout_top_row.setAlignment(QtCore.Qt.AlignLeft)
        self.main_layout.addLayout(layout_top_row)

        # LIVE
        self.live_button = QtWidgets.QPushButton('LIVE')
        self.live_button.setFixedSize(buttonWidth, buttonHeight)
        self.live_button.clicked.connect(self.toggle_live)
        layout_top_row.addWidget(self.live_button)

        # RECORD
        self.record_button = QtWidgets.QPushButton('RECORD')
        self.record_button.setFixedSize(buttonWidth, buttonHeight)
        self.record_button.clicked.connect(self.toggle_recording)
        layout_top_row.addWidget(self.record_button)

        # WORKING FOLDER
        self.working_folder = 'E:\\Duncan\\'
        output_path_label = QtWidgets.QLabel('Output path:')
        layout_top_row.addWidget(output_path_label)
        self.working_folder_label = QtWidgets.QLabel(self.working_folder)
        self.working_folder_label.setStyleSheet("QLabel { text-align: right; }")
        layout_top_row.addWidget(self.working_folder_label)

        # FILENAME
        self.filename_le = QtWidgets.QLineEdit()
        self.filename_le.setPlaceholderText('Enter file name')
        layout_top_row.addWidget(self.filename_le)

        # CHANGE WORKING FOLDER
        change_working_folder_button = QtWidgets.QPushButton('change directory')
        change_working_folder_button.clicked.connect(self.change_working_folder)
        layout_top_row.addWidget(change_working_folder_button)

        # -----------------------------------
        # Data plots: can be designed by user
        # -----------------------------------

        # Create a GraphicsLayoutWidget to add plots
        layout_data_proxy = QtWidgets.QHBoxLayout()
        self.layout_data_plots = pg.GraphicsLayoutWidget()
        layout_data_proxy.addWidget(self.layout_data_plots)
        self.main_layout.addLayout(layout_data_proxy)

        # IMAGE PLOT
        self.img = pg.ImageItem()
        self.img_plot = self.layout_data_plots.addPlot(row=0, col=0)
        self.img_plot.setMouseEnabled(False, False)
        self.img_plot.setAspectLocked()
        self.img_plot.hideAxis('bottom')
        self.img_plot.hideAxis('left')
        self.img_plot.addItem(self.img)

        # ---------------------------------------------------------------
        # Camera info: [CHANGE SETTINGS] [CAMERA INFO] | [BUFFER] | [REC]
        # ---------------------------------------------------------------

        layout_camera_info = QtWidgets.QHBoxLayout()
        layout_settings = QtWidgets.QHBoxLayout()
        layout_buffer = QtWidgets.QHBoxLayout()
        layout_rec = QtWidgets.QHBoxLayout()
        layout_camera_info.addLayout(layout_settings, 2)
        layout_camera_info.addLayout(layout_buffer, 1)
        layout_camera_info.addLayout(layout_rec, 1)
        self.main_layout.addLayout(layout_camera_info)

        # CHANGE SETTINGS
        self.camera_settings_button = QtWidgets.QPushButton('Camera settings')
        self.camera_settings_button.setFixedSize(buttonWidth, buttonHeight)
        self.camera_settings_button.clicked.connect(self.change_camera_settings)
        layout_settings.addWidget(self.camera_settings_button)

        # CAMERA INFO
        self.camera_info_text = 'frame size: {0}, frame rate: {1} / {2} fps'
        self.camera_info_label = QtWidgets.QLabel(self.camera_info_text.format(str(self.frameSize),
                                                                               str(0),
                                                                               str(self.frameRate)))
        layout_settings.addWidget(self.camera_info_label)

        # BUFFER
        buffer_label = QtWidgets.QLabel('Frame buffer:')
        self.buffer_bar = QtWidgets.QProgressBar()
        layout_buffer.addWidget(buffer_label)
        layout_buffer.addWidget(self.buffer_bar)

        # REC
        self.rec_label_text = 'Recording time (seconds): {0}.{1}'
        self.rec_label = QtWidgets.QLabel(self.rec_label_text.format(0, 0))
        layout_rec.addWidget(self.rec_label)

        # ----------
        # Status bar
        # ----------
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('idle')

    def _spawn_camera_thread(self):
        self.camera_thread = CameraThread(self.frameSize, self.frameRate)
        self.camera_thread.newframe.connect(self.receive_frame)
        self.camera_thread.start()
        CameraWaitMessage.run(self)

    def _spawn_tracking_thread(self):
        """Spawns a thread for tracking"""
        ret = self.tracker_init()
        if ret:
            self.tracking_thread = TrackerThread(self.tracker, self.frame_cache_input, self.frame_cache_output,
                                                 *self.caches, **self.tracking_kwargs)
            self.tracking_thread.start()
        return ret

    def _join_tracking_thread(self):
        try:
            self.tracking_thread.exit_flag = True
            self.tracking_thread.join()
        except AttributeError:
            return

    def _spawn_saving_thread(self):
        """Spawns a thread for saving data"""
        fname = str(self.filename_le.text())
        if len(fname) == 0:  # empty filename check
            fname, ok = QtWidgets.QInputDialog.getText(self, 'Enter file name', 'Enter file name:')
            fname = str(fname)
            if ok and (len(fname) > 0):
                self.filename_le.setText(str(fname))
            else:
                return False
        output_path = os.path.join(self.working_folder, fname)
        if os.path.exists(output_path + '.avi'):  # overwrite check
            msg = 'File {} already exists.'.format(output_path + '.avi')
            QtWidgets.QMessageBox.information(self, 'Information', msg, QtWidgets.QMessageBox.Ok)
            return False
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.writer = cv2.VideoWriter(output_path + '.avi', fourcc, self.frameRate, self.frameSize, False)
        self.saving_kwargs['path'] = output_path
        self.saving_thread = SaverThread(self.saver, self.writer, self.frame_cache_output,
                                         *self.caches, **self.saving_kwargs)
        self.saving_thread.finished.connect(self._release_writer)
        self.saving_thread.start()
        return True

    def _release_writer(self):
        self.writer.release()

    def _join_saving_thread(self):
        try:
            self.saving_thread.exit_flag = True
            self.status_bar.showMessage('saving...')
            if self.saving_thread.isRunning():
                SaveProgressWindow.run(self)
        except AttributeError:
            return

    def _clear_caches(self):
        self.frame_cache_input.clear()
        self.frame_cache_output.clear()
        for cache in self.caches:
            cache.clear()

    def start_live(self):
        # Handle threads
        self._clear_caches()
        check = self._spawn_tracking_thread()  # check that tracking thread started correctly
        if check:
            self.camera_thread.acquiring = True
            # Update GUI
            self.live_button.setText('STOP')
            self.record_button.setEnabled(False)
            self.status_bar.showMessage('live')

    def stop_live(self):
        # Handle threads
        self.camera_thread.acquiring = False
        self._join_tracking_thread()
        self._clear_caches()
        # Update GUI
        self.live_button.setText('LIVE')
        self.record_button.setEnabled(True)
        self._change_camera_message()
        self.status_bar.showMessage('idle')

    def toggle_live(self):
        """Code executed when the LIVE button is toggled"""
        if not self.camera_thread.acquiring:  # Start live
            self.start_live()
        else:  # Stop live
            self.stop_live()

    def start_recording(self):
        # Handle threads
        self._clear_caches()
        check1 = self._spawn_tracking_thread()  # check that tracking thread started correctly
        if check1:
            check2 = self._spawn_saving_thread()  # check that saving thread started correctly
            if check2:
                self.camera_thread.acquiring = True
                self.recording_start_time = datetime.datetime.now()
                # Update GUI
                self.record_button.setText('STOP')
                self.live_button.setEnabled(False)
                self.filename_le.setEnabled(False)
                self.status_bar.showMessage('recording...')

    def stop_recording(self):
        # Handle threads
        self.camera_thread.acquiring = False
        self._join_tracking_thread()
        self._join_saving_thread()
        # Update GUI
        self.record_button.setText('RECORD')
        self.live_button.setEnabled(True)
        self.filename_le.setEnabled(True)
        self._change_camera_message()
        self.status_bar.showMessage('idle')

    def toggle_recording(self):
        """Code executed when the RECORD button is toggled"""
        if not self.camera_thread.acquiring:  # Start recording
            self.start_recording()
        else:  # Stop recording
            self.stop_recording()

    def receive_frame(self, frame_tuple):
        """Code executed whenever a new frame is received from the CameraThread"""
        # Add frame to the input cache
        frame_number, timestamp, frame = frame_tuple
        self.frame_cache_input.append([frame_number, timestamp, frame])

    def change_working_folder(self):
        working_folder = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select directory', 'E:/')
        working_folder = str(working_folder)
        if working_folder != '':
            self.working_folder = working_folder + '\\'
            self.working_folder_label.setText(self.working_folder)

    def change_camera_settings(self):
        if self.camera_thread.acquiring:
            return
        ret, new_settings = CameraSettings.change(self.frameSize, self.frameRate)
        if ret:
            self.frameSize = new_settings['wh']
            self.frameRate = new_settings['fps']
            self.camera_thread.connected = False
            self.camera_thread.wait()
            self._spawn_camera_thread()
            self._change_camera_message()

    def closeEvent(self, event):
        # Make sure cameras thread exits properly before closing
        print('Exiting')
        self.camera_thread.connected = False
        self._join_tracking_thread()
        self._join_saving_thread()
        self.camera_thread.wait()
        event.accept()

    def _change_camera_message(self):
        try:
            n = min(len(self.frame_cache_output), 100)
            diff = self.frame_cache_output[n - 1][1] - self.frame_cache_output[0][1]
            fps = int(n / diff)
        except (IndexError, ZeroDivisionError):
            fps = self.frameRate
        try:
            if self.saving_thread.isRunning():
                buffer_usage = 100 * float(len(self.frame_cache_output) / self._frame_buffer)
                # Show how long current recording has been running
                now = datetime.datetime.now()
                delta = now - self.recording_start_time
                sec = delta.seconds
                ms = int(delta.microseconds / 1000.)
                self.rec_label.setText(self.rec_label_text.format(sec, ms))
            else:
                buffer_usage = 0
        except AttributeError:
            buffer_usage = 0
        message = self.camera_info_text.format(self.frameSize, fps, self.frameRate)
        self.buffer_bar.setValue(buffer_usage)
        self.camera_info_label.setText(message)

    def tracker_init(self):
        """Method defined in subclass to initialise tracking"""
        return True

    def update_plots(self):
        """Code executed to update plots. Can be overridden in subclasses."""
        if self.camera_thread.acquiring:
            try:
                # Show the new image
                i, timestamp, img = self.frame_cache_output[-1]
                img = np.asarray(img / np.max(img))
                self.img.setImage(img[::-1, :].T)
                # Update cameras and buffer info
                self._change_camera_message()
            except IndexError:  # No data to show
                return
