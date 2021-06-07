from pydra.core import Worker
from tailtracker import TailTracker


class TailTrackingWorker(Worker):

    name = "tail"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events["initialize_tracker"] = self.init_tracker
        self.events["set_parameters"] = self.set_parameters

    def setup(self):
        self.tracker = TailTracker(None, None, None)

    def recv_frame(self, t, i, frame, **kwargs):
        angle = self.tracker.track(frame)
        data = {"angle": None, "points": []}
        if angle is not None:
            data["angle"] = angle
            data["points"] = [[int(p[0]), int(p[1])] for p in self.tracker.points]
        self.send_indexed(t, i, data)

    def init_tracker(self, points, n, **kwargs):
        background = kwargs.get("background", self.tracker.background)
        ksize = kwargs.get("ksize", self.tracker.ksize)
        n_tip_points = kwargs.get("n_tip_points", self.tracker.n_tip_points)
        self.tracker = TailTracker.from_points(points, n, background=background, ksize=ksize, n_tip_points=n_tip_points)

    def set_parameters(self, **kwargs):
        background = kwargs.get("background", self.tracker.background)
        ksize = kwargs.get("ksize", self.tracker.ksize)
        n_tip_points = kwargs.get("n_tip_points", self.tracker.n_tip_points)
        self.tracker.background = background
        self.tracker.ksize = ksize
        self.tracker.n_points = n_tip_points
