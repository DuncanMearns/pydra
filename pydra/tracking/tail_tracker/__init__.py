from ...core import Plugin, TrackingWorker, TrackingOutput
from ...gui.display import Plotter
from .widgets import TailTrackingWidget

import numpy as np
import cv2
from collections import deque


class TailTracker(TrackingWorker):

    def __init__(self, start_xy, tail_length, n_points, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_xy = start_xy
        self.tail_length = tail_length
        self.n_points = n_points

    def track(self, frame_number, timestamp, frame):
        if (self.start_xy is not None) and (self.tail_length is not None):
            frame = np.asarray(frame / np.max(frame))
            width = self.tail_length
            x = self.start_xy[0]
            y = self.start_xy[1]
            tail_points = [[x, y]]
            img_filt = np.zeros(frame.shape)
            img_filt = cv2.boxFilter(frame, -1, (7, 7), img_filt)
            lin = np.linspace(0, np.pi, 20)
            for j in range(self.n_points):
                try:
                    # Find the x and y values of the arc
                    xs = x + width / self.n_points * np.sin(lin)
                    ys = y + width / self.n_points * np.cos(lin)
                    # Convert them to integer, because of definite pixels
                    xs, ys = xs.astype(int), ys.astype(int)
                    # ident = np.where(img_filt[ys,xs]==max(img_filt[ys,xs]))[0][0]
                    ident = np.where(img_filt[ys, xs] == min(img_filt[ys, xs]))[0][0]
                    x = xs[ident]
                    y = ys[ident]
                    lin = np.linspace(lin[ident] - np.pi / 2, lin[ident] + np.pi / 2, 20)
                    # Add point to list
                    tail_points.append([x, y])
                except IndexError:
                    tail_points.append(tail_points[-1])
            tailangle = float(np.arctan2(np.nanmean(np.asarray(tail_points)[-3:-1, 1]) -
                                         np.asarray(tail_points)[0, 1],
                                         np.nanmean(np.asarray(tail_points)[-3:-1, 0]) -
                                         np.asarray(tail_points)[0, 0]) * 180.0 / 3.1415) * (-1)
            data_output = dict(points=tail_points, angle=tailangle)
            return TrackingOutput(frame_number, timestamp, frame, data_output)
        else:
            return super().track(frame_number, timestamp, frame)


class TailPlotter(Plotter):

    def __init__(self, parent, name):
        super().__init__(parent, name)
        # Add tail point plot to main display
        self.points_data = self.parent.plots["main"].plot([], [], pen=None, symbol='o')
        # Add tail angle data to tracking plot
        self.cache_size = 5000
        self.cache = deque(maxlen=self.cache_size)
        self.t0 = 0
        self.angle_data = self.plot.plot([], [])

    def reset(self):
        self.t0 = 0
        self.cache.clear()

    def update(self, *args, **kwargs):
        last = args[-1]
        if last.data:
            # Plot points
            frame = last.frame
            points = np.asarray(last.data["points"])
            self.points_data.setData(points[:, 0], frame.shape[1] - points[:, 1])
            # Plot tail angle
            if not self.t0:
                self.t0 = args[0].timestamp
            for output in args:
                self.cache.append((output.timestamp - self.t0, output.data["angle"]))
            show_angles = np.array(self.cache)
            self.angle_data.setData(show_angles[:, 0], show_angles[:, 1])


class TailTrackerPlugin(Plugin):

    name = 'TailTracker'
    worker = TailTracker
    params = {'start_xy': None,
              'tail_length': None,
              'n_points': 9}
    widget = TailTrackingWidget
    plotter = TailPlotter

    def __init__(self, plugin, *args, **kwargs):
        super().__init__(plugin, *args, **kwargs)

    def update_tail_points(self, new_points):
        points = np.asarray(new_points)
        length = np.linalg.norm(points) + 10
        self.params['start_xy'] = points[0]
        self.params['tail_length'] = length
        self.paramsChanged.emit(self.name, (('start_xy', self.params['start_xy']),
                                            ('tail_length', self.params['tail_length'])))

    def update_n_points(self, n):
        self.params['n_points'] = n
        self.paramsChanged.emit(self.name, (('n_points', n),))
