from ..core import TrackingWorker, TrackingOutput, Plugin


class DummyTracker(TrackingWorker):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def track(self, frame_number, timestamp, frame):
        return TrackingOutput(frame_number, timestamp, frame, {})


class NoTracking(Plugin):

    name = 'DummyTracker'
    worker = DummyTracker
    widget = None
