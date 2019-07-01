import threading
import time


class TrackerThread(threading.Thread):
    """Python thread for helpers frames

    Parameters
    ----------
    tracker : Tracker object
        A helpers object that has a track_frame method, which takes a frame as input and returns helpers output as an
        iterable.
    frame_input : collections.deque
        Cache containing newly acquired frames as timestamped tuples.
    frame_output : collections.deque
        Cache where newly tracked frames are added.
    *args : iterable
        User-defined caches which receive output of helpers object's track_frame method.
    **kwargs : dict
        Keyword arguments passed to the tracker object.
    """

    def __init__(self, frame_input_cache, *args):
        super().__init__()
        self.frame_input_cache = frame_input_cache
        self.trackers = args
        self.exit_flag = False

    def run(self):
        while not self.exit_flag:
            try:
                frame_tuple = self.frame_input_cache.popleft()
                for tracker in self.trackers:
                    tracker.track(*frame_tuple)
            except IndexError:
                time.sleep(0.02)
