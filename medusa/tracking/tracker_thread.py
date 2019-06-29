import threading
import time


class TrackerThread(threading.Thread):
    """Python thread for tracking frames

    Parameters
    ----------
    tracker : object
        A tracking object that has a track_frame method, which takes a frame as input and returns tracking output as an
        iterable.
    frame_input : collections.deque
        Cache containing newly acquired frames as timestamped tuples.
    frame_output : collections.deque
        Cache where newly tracked frames are added.
    *args : iterable
        User-defined caches which receive output of tracking object's track_frame method.
    **kwargs : dict
        Keyword arguments passed to the tracker object.
    """

    def __init__(self, tracker, frame_input, frame_output, *args, **kwargs):
        super(TrackerThread, self).__init__()
        self.tracker = tracker(**kwargs)
        self.frame_input = frame_input
        self.frame_output = frame_output
        self.caches = args
        self.exit_flag = False

    def run(self):
        while not self.exit_flag:
            try:
                frame_tuple = self.frame_input.popleft()
                tracking_output = self.tracker.track_frame(*frame_tuple)
                self.frame_output.append(frame_tuple)
                for tracking_data, cache in zip(tracking_output, self.caches):
                    cache.append(tracking_data)
            except IndexError:
                time.sleep(0.02)
