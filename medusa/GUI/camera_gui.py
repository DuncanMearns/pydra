from ..camera import *
from ..camera.cameras.pike import CameraThread
from ..helpers.threads import *
from ..helpers.trackers import _CameraBase
from ..helpers.GUI_helpers import *
from PyQt5 import QtCore, QtWidgets
import pyqtgraph as pg
from collections import deque
import os
import datetime
import numpy as np


class CameraGUI(QtWidgets.QMainWindow):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # ==============
        # SETUP TRACKERS
        # ==============

        self.buffer_display = 10000
        self.buffer_tracking = 1000
        self.buffer_temp = 10

        self.frame_input_cache = deque(maxlen=self.buffer_tracking)
        self.frame_output_cache = deque(maxlen=self.buffer_tracking)

        self.video_tracker = _CameraBase(self)
        self.trackers = [self.video_tracker]
        self.gui_update_methods = [self.update_image]
        self.gui_constructor_methods = [self.add_image_plot]

        # ============
        # SETUP CAMERA
        # ============

        # Start the cameras thread
        self.frame_size = (340, 240)  # (width, height)
        self.frame_rate = 300  # fps
        self._spawn_camera_thread()

        # ==========================
        # SETUP DISPLAY UPDATE TIMER
        # ==========================

        # Create timer for handling display updates
        # This ensures that events sent from recording or helpers threads don't queue up waiting to be processed
        self.display_update_rate = 20  # fps
        self.timer = QtCore.QTimer()
        self.timer.setInterval(int(1000 / self.display_update_rate))
        self.timer.timeout.connect(self.update_plots)
        self.timer.start()

        # =================
        # SETUP MAIN WINDOW
        # =================

        # Layout sizes
        self.main_width = 1000
        self.main_height = 800
        self.button_width = 100
        self.button_height = 20

        # Setup main window
        self.resize(self.main_width, self.main_height)
        self.w = QtWidgets.QWidget()
        self.setCentralWidget(self.w)

        self.main_layout = QtWidgets.QVBoxLayout()
        self.w.setLayout(self.main_layout)

        # ===================
        # EXPERIMENT PROTOCOL
        # ===================
        self.protocol = None

        # ----------------------------------------------------------------------------
        # Top dock: [LIVE] [RECORD] [WORKING FOLDER] [FILENAME] [CHANGE WORKING FOLDER]
        # ----------------------------------------------------------------------------

        # Setup top dock
        self.dock_top = QtWidgets.QDockWidget('Live | Record')
        self.dock_top.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.dock_top_widget = QtWidgets.QWidget()
        self.dock_top.setWidget(self.dock_top_widget)
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea, self.dock_top)
        layout_dock_top = QtWidgets.QHBoxLayout()
        layout_dock_top.setAlignment(QtCore.Qt.AlignLeft)
        self.dock_top_widget.setLayout(layout_dock_top)

        # LIVE
        self.live_button = QtWidgets.QPushButton('LIVE')
        self.live_button.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPlay')))
        self.live_button.setFixedSize(self.button_width, self.button_height)
        self.live_button.clicked.connect(self.toggle_live)
        layout_dock_top.addWidget(self.live_button)

        # RECORD
        self.record_button = QtWidgets.QPushButton('RECORD')
        self.record_button.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_DialogNoButton')))
        self.record_button.setFixedSize(self.button_width, self.button_height)
        self.record_button.clicked.connect(self.toggle_recording)
        layout_dock_top.addWidget(self.record_button)

        # WORKING FOLDER
        self.working_folder = 'E:\\Duncan\\'
        output_path_label = QtWidgets.QLabel('Output path:')
        layout_dock_top.addWidget(output_path_label)
        self.working_folder_label = QtWidgets.QLabel(self.working_folder)
        self.working_folder_label.setStyleSheet("QLabel { text-align: right; }")
        layout_dock_top.addWidget(self.working_folder_label)

        # FILENAME
        self.filename_le = QtWidgets.QLineEdit()
        self.filename_le.setPlaceholderText('Enter file name')
        layout_dock_top.addWidget(self.filename_le)

        # CHANGE WORKING FOLDER
        change_working_folder_button = QtWidgets.QPushButton('Change directory')
        change_working_folder_button.clicked.connect(self.change_working_folder)
        layout_dock_top.addWidget(change_working_folder_button)

        # ---------------------------------------
        # Data plots: can be designed in subclass
        # ---------------------------------------
        # Create a GraphicsLayoutWidget to add plots
        layout_user_proxy = QtWidgets.QHBoxLayout()
        self.layout_user_plots = pg.GraphicsLayoutWidget()
        layout_user_proxy.addWidget(self.layout_user_plots)
        self.main_layout.addLayout(layout_user_proxy)

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
        self.camera_settings_button.setFixedSize(self.button_width, self.button_height)
        self.camera_settings_button.clicked.connect(self.change_camera_settings)
        layout_settings.addWidget(self.camera_settings_button)

        # CAMERA INFO
        self.camera_info_text = 'frame size: {0}, frame rate: {1} / {2} fps'
        self.camera_info_label = QtWidgets.QLabel(self.camera_info_text.format(str(self.frame_size),
                                                                               str(0),
                                                                               str(self.frame_rate)))
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

    def _add_features_dock(self):
        self.dock_right = QtWidgets.QDockWidget('Control panel')
        self.dock_right.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.dock_right_widget = QtWidgets.QWidget()
        self.dock_right.setWidget(self.dock_right_widget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock_right)
        self.layout_features = QtWidgets.QVBoxLayout()
        self.layout_features.setAlignment(QtCore.Qt.AlignTop)
        self.dock_right_widget.setLayout(self.layout_features)

    def _spawn_camera_thread(self):
        """Starts the camera daemon thread"""
        self.camera_thread = CameraThread(self.frame_size, self.frame_rate)
        self.camera_thread.newframe.connect(self.receive_frame)
        self.camera_thread.start()
        CameraWaitMessage.run(self)

    def receive_frame(self, frame_tuple):
        """Code executed whenever a new frame is received from the CameraThread"""
        # Add frame to the input cache
        frame_number, timestamp, frame = frame_tuple
        self.frame_input_cache.append([frame_number, timestamp, frame])

    def _initialise_tracking(self):
        """Method defined in subclass called to initialise helpers"""
        for tracker in self.trackers:
            ret = tracker.initialise_tracking()
            if not ret:
                return False
        return True

    def _spawn_tracking_thread(self):
        """Spawns a thread for helpers"""
        ret = self._initialise_tracking()
        if ret:
            self.tracking_thread = TrackerThread(self.frame_input_cache, *self.trackers)
            self.tracking_thread.start()
        return ret

    def _join_tracking_thread(self):
        """Safely joins the helpers thread to the main thread"""
        try:
            self.tracking_thread.exit_flag = True
            self.tracking_thread.join()
        except AttributeError:
            return

    def _initialise_saving(self, output_path):
        for tracker in self.trackers:
            ret = tracker.initialise_saving(output_path)
            if not ret:
                self._cleanup_saving()
                return False
        return True

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
        ret = self._initialise_saving(output_path)
        if ret:
            self.saving_thread = SaverThread(output_path, *self.trackers)
            self.saving_thread.finished.connect(self._cleanup_saving)
            self.saving_thread.start()
            return True
        else:
            return False

    def _cleanup_saving(self):
        """Releases the current video writer object"""
        for tracker in self.trackers:
            tracker.cleanup_saving()

    def _join_saving_thread(self):
        """Safely joins the saving thread to the main thread"""
        try:
            self.saving_thread.exit_flag = True
            self.status_bar.showMessage('saving...')
            if self.saving_thread.isRunning():
                SavingWindow.run(self)
        except AttributeError:
            return

    def _clear_caches(self):
        """Clears all caches"""
        self.frame_input_cache.clear()
        self.frame_output_cache.clear()
        for tracker in self.trackers:
            tracker.clear()

    def start_live(self):
        """Starts a live stream from the camera"""
        self._clear_caches()
        check = self._spawn_tracking_thread()  # check that helpers thread started correctly
        if check:
            self.camera_thread.acquiring = True
            # Update GUI
            self.live_button.setText('STOP')
            self.live_button.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPause')))
            self.record_button.setEnabled(False)
            self.status_bar.showMessage('live')

    def stop_live(self):
        """Stops a live stream from the camera"""
        # Handle threads
        self.camera_thread.acquiring = False
        self._join_tracking_thread()
        # Update GUI
        self.live_button.setText('LIVE')
        self.live_button.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPlay')))
        self.record_button.setEnabled(True)
        self._change_camera_message()
        self.status_bar.showMessage('idle')

    def toggle_live(self):
        """Toggles a live stream from the camera"""
        if not self.camera_thread.acquiring:  # start live stream
            self.start_live()
        else:  # stop live stream
            self.stop_live()

    def start_recording(self):
        """Starts a recording"""
        # Handle threads
        self._clear_caches()
        check1 = self._spawn_tracking_thread()  # check that helpers thread started correctly
        if check1:
            check2 = self._spawn_saving_thread()  # check that saving thread started correctly
            if check2:
                self.camera_thread.acquiring = True
                self.recording_start_time = datetime.datetime.now()
                if self.protocol is not None:
                    self.protocol.start()
                # Update GUI
                self.record_button.setText('STOP')
                self.record_button.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaStop')))
                self.live_button.setEnabled(False)
                self.filename_le.setEnabled(False)
                self.status_bar.showMessage('recording...')

    def stop_recording(self):
        """Stops a recording"""
        # Handle threads
        self.camera_thread.acquiring = False
        self._join_tracking_thread()
        self._join_saving_thread()
        # Update GUI
        self.record_button.setText('RECORD')
        self.record_button.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_DialogNoButton')))
        self.live_button.setEnabled(True)
        self.filename_le.setEnabled(True)
        self._change_camera_message()
        self.status_bar.showMessage('idle')

    def toggle_recording(self):
        """Toggles a recording"""
        if not self.camera_thread.acquiring:  # start recording
            self.start_recording()
        else:  # stop recording
            self.stop_recording()

    def change_working_folder(self):
        """Opens a file dialog to select a new working folder for saving"""
        working_folder = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select directory', 'E:/')
        working_folder = str(working_folder)
        if working_folder != '':
            self.working_folder = working_folder + '\\'
            self.working_folder_label.setText(self.working_folder)

    def _change_camera_message(self):
        try:
            if len(self.video_tracker.timestamp_cache) > 1:
                delta = self.video_tracker.timestamp_cache[-1] - self.video_tracker.timestamp_cache[0]
                fps = int(len(self.video_tracker.timestamp_cache) / delta)
            else:
                fps = self.frame_rate
        except (ZeroDivisionError, IndexError, ValueError):
            fps = self.frame_rate
        try:
            if self.saving_thread.isRunning():
                buffer_usage = 100 * float(len(self.frame_output_cache) / self.buffer_tracking)
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
        message = self.camera_info_text.format(self.frame_size, fps, self.frame_rate)
        self.buffer_bar.setValue(buffer_usage)
        self.camera_info_label.setText(message)

    def change_camera_settings(self):
        """Opens a dialog window where camera settings can be adjusted and restarts the camera thread"""
        if self.camera_thread.acquiring:  # do nothing if acquisition from camera in progress
            return
        ret, new_settings = CameraSettings.change(self.frame_size, self.frame_rate)
        if ret:
            self.frame_size = new_settings['wh']
            self.frame_rate = new_settings['fps']
            self.camera_thread.connected = False
            self.camera_thread.wait()
            self._spawn_camera_thread()
            self._change_camera_message()

    def closeEvent(self, event):
        # Make sure cameras thread exits properly before closing
        print('Exiting')
        self.camera_thread.connected = False
        self._join_tracking_thread()
        print('Tracking thread joined')
        self._join_saving_thread()
        print('Saving thread joined')
        self.camera_thread.wait()
        print('Disconnected from camera')
        self.parent().show()
        event.accept()

    def add_image_plot(self, **kwargs):
        """Adds a plot for displaying images from the camera to the GUI

        Parameters
        ----------
        row : int
            row number passed to GraphicsLayoutWidget addPlot method
        col : int
            column number passed to GraphicsLayoutWidget addPlot method
        """
        self.image = pg.ImageItem()
        self.image_plot = self.layout_user_plots.addPlot(**kwargs)
        self.image_plot.setMouseEnabled(False, False)
        self.image_plot.setAspectLocked()
        self.image_plot.hideAxis('bottom')
        self.image_plot.hideAxis('left')
        self.image_plot.addItem(self.image)

    def add_gui_components(self):
        """Constructs data and other components of the GUI in subclasses."""
        for add_component in self.gui_constructor_methods:
            add_component()

    def update_image(self):
        try:
            # Show the new image
            img = self.video_tracker.display_cache[-1]
            img = np.asarray(img / np.max(img))
            self.image.setImage(img[::-1, :].T)
            # Update cameras and buffer info
            self._change_camera_message()
        except IndexError:  # No data to show
            return

    def update_plots(self):
        """Code executed to update plots. Can be overridden in subclasses."""
        if self.camera_thread.acquiring:
            for update in self.gui_update_methods:
                update()
