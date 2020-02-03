from .camera_gui import CameraGUI
from ..helpers.trackers import TailTracker
from ..helpers.GUI_helpers.lines import HorizontalLine
from PyQt5 import QtWidgets
import numpy as np


class TailTrackerGUI(CameraGUI):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Tail tracker')
        self.resize(1000, 800)
        # ----------
        # SET HELPER
        # ----------
        self.tail_tracker = TailTracker(self, self.buffer_tracking, self.buffer_temp, self.buffer_display)
        self.trackers.append(self.tail_tracker)
        self.gui_update_methods.append(self.update_tail_plots)
        self.gui_constructor_methods.append(self.add_tail_tracking_features)

    def reset_tail_tracking(self):
        self.tail_tracker.initialise_tracking(True)

    def add_tail_tracking_features(self, **kwargs):
        if not 'layout_features' in dir(self):
            self._add_features_dock()
        # Reset tail tracking
        layout_tail_tracking = QtWidgets.QVBoxLayout()
        layout_tail_tracking.addWidget(QtWidgets.QLabel('Tail tracking'))
        self.tail_points_button = QtWidgets.QPushButton('Set tail points')
        self.tail_points_button.setFixedSize(self.button_width, 2 * self.button_height)
        self.tail_points_button.clicked.connect(self.reset_tail_tracking)
        layout_tail_tracking.addWidget(self.tail_points_button)
        self.layout_features.addLayout(layout_tail_tracking)
        self.layout_features.addWidget(HorizontalLine())
        # Tail points
        self.tail_points = self.image_plot.plot([], [], pen=None, symbol='o')
        # Tail angle
        self.layout_user_plots.nextRow()
        self.tail_angle_plot = self.layout_user_plots.addPlot(**kwargs)
        self.tail_angle_plot.showGrid(x=True, y=True)
        self.tail_angle_plot.setLabel('left', 'Tail angle', 'deg')
        # TODO: Set up auto-pan so that it keeps up with the most recently acquired frames
        self.tail_angle_plot.setRange(yRange=[-30, 30])
        self.tail_angle_plot.setAutoPan(x=True)
        self.tail_angle_plot.setLimits(minXRange=1000)
        self.tail_angle = self.tail_angle_plot.plot([], [], pen=(255, 0, 0))

    def update_tail_plots(self):
        try:
            # Show tail points
            tail_points = self.tail_tracker.points_display_cache[-1]
            self.tail_points.setData(tail_points[:, 0], self.frame_size[1] - tail_points[:, 1])
            # Update tail angle
            tail_angle = np.array(self.tail_tracker.angle_display_cache)
            t = np.arange(len(tail_angle))
            self.tail_angle.setData(t, tail_angle)
        except IndexError:  # No data to show
            return
