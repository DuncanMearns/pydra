from ..core import TrackingWorker, TrackingOutput


class DummyTracker(TrackingWorker):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def track(self, frame_number, timestamp, frame):
        return TrackingOutput(frame_number, timestamp, frame, None)
