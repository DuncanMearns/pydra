from ..process import TrackingWorker, TrackingOutput


class DummyTracker(TrackingWorker):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def track(self, frame_number, timestamp, frame):
        return TrackingOutput(frame_number, timestamp, frame, None)
