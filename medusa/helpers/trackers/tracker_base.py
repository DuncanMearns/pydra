class TrackerBase():

    def __init__(self, parent, *args, **kwargs):
        super().__init__()
        self.parent = parent
        self.saving_flag = False

    def clear(self):
        """Method called when caches are cleared."""
        return

    def initialise_tracking(self):
        """Method called by main thread at start of live stream and recording."""
        return True

    def track(self, frame_number, timestamp, frame):
        """Method called when a new frame is available to track."""
        return

    def cleanup_tracking(self):
        """Method called by main thread at end of live stream and recording."""

    def initialise_saving(self, path):
        """Method called by main thread at start of recording."""
        return True

    def extend(self, frame_data):
        """Method called when new tracking data is available to save."""
        self.saving_flag = True
        return

    def dump(self):
        """Method called by saving thread at end of recording."""
        return

    def cleanup_saving(self):
        """Method called by main thread at end of recording."""
        return
