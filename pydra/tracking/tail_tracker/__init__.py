from ...core import Plugin, TrackingWorker, TrackingOutput
from .widgets import TailTrackingWidget
import numpy as np
import cv2


class TailTracker(TrackingWorker):

    def __init__(self, start_xy, tail_length, n_points, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_xy = start_xy
        self.tail_length = tail_length
        self.n_points = n_points

    def track(self, frame_number, timestamp, frame):
        if (self.start_xy is not None) and (self.tail_length is not None):
            frame = np.asarray(frame / np.max(frame))
            tail_points = [self.start_xy]
            width = self.tail_length
            x = self.start_xy[0]
            y = self.start_xy[1]
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


class TailTrackerPlugin(Plugin):

    name = 'TailTracker'
    worker = TailTracker
    widget = TailTrackingWidget

    def __init__(self, plugin, *args, **kwargs):
        super().__init__(plugin, *args, **kwargs)
        self.params['start_xy'] = None
        self.params['tail_length'] = None
        self.params['n_points'] = 9

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
