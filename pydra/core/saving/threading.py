import threading
import queue
import cv2
from pathlib import Path
from collections import deque
import pandas as pd


class Thread(threading.Thread):
    """Base thread class for saving data.

    Implements a run method. The run method calls setup, then enters a loop where the queue is continually checked for
    new data, which are then handled by a dump method. When an exit signal (that evaluates as False) is received, the
    loop exits and a cleanup method is called.

    Parameters
    ----------
    path : str
        The path where data are to be saved.
    q : queue.Queue
        Queue containing data.
    """

    def __init__(self, path: str, q: queue.Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = str(path)
        self.q = q

    def setup(self):
        return

    def dump(self, *args):
        return

    def cleanup(self):
        return

    def run(self):
        self.setup()
        while True:
            try:
                data = self.q.get(timeout=0.01)
                if data:
                    self.dump(*data)
                else:
                    break
            except queue.Empty:
                pass
        self.cleanup()


class FrameThread(Thread):
    """Thread for saving video data using opencv.

    Parameters
    ----------
    path : str
        File path where video is to be saved.
    q : queue.Queue
        Queue that contains serialized frame data.
    frame_rate : float
        Frame rate at which video is to be saved.
    frame_size : tuple (width, height)
        The width and height of the frames.
    fourcc : str
        Compression codec.
    is_color : bool (default is False)
        Whether frames are in color.

    Attributes
    ----------
    writer : cv2.VideoWriter
        The opencv video writer object.
    """

    def __init__(self, path: str, q: queue.Queue, frame_rate: float, frame_size: tuple, fourcc: str,
                 is_color: bool = False, *args, **kwargs):
        super().__init__(path, q, *args, **kwargs)
        self.frame_rate = frame_rate
        self.frame_size = frame_size
        self.fourcc = fourcc
        self.is_color = is_color
        self.writer = None

    def setup(self):
        """Creates the video writer object."""
        fourcc = cv2.VideoWriter_fourcc(*self.fourcc)
        self.writer = cv2.VideoWriter(self.path, fourcc, self.frame_rate, self.frame_size, self.is_color)

    def dump(self, source, frame):
        """Saves frames.

        Parameters
        ----------
        source : str
            The source of the video frames. Parameter not used and exists only for consistency with other classes.
        frame : np.ndarray
        """
        self.writer.write(frame)

    def cleanup(self):
        """Releases the video writer object."""
        self.writer.release()


class IndexedThread(Thread):
    """Thread for saving indexed data.

    Data are stored in the data attribute and saved as a pandas DataFrame during cleanup. The data attribute is a
    nested dictionary. The top level contains the source of incoming data. The next level contains three keys: "time",
    "index" and "data". The "time" and "index" are lists; "data" is a dictionary of lists for each data parameter.

    Parameters
    ----------
    path : str
        Csv file path where data is to be saved.
    q : queue.Queue
        Queue that contains serialized indexed data.

    Attributes
    ----------
    data : dict
        Dictionary where incoming data are stored.
    """

    def __init__(self, path, q, *args, **kwargs):
        super().__init__(path, q, *args, **kwargs)
        self.data = None

    def setup(self):
        """Initializes the data attribute."""
        self.data = {}

    def dump(self, source, t, i, data):
        """Sorts and places data into the data dictionary.

        Parameters
        ----------
        source : str
            The source (i.e. worker name) of the data.
        t : float
        i : int
        data : dict
        """
        for param, val in data.items():  # add parameter values to the data dictionary with key source.param
            k = ".".join([source, param])
            if k in self.data:
                self.data[k].append((t, i, val))
            else:
                self.data[k] = [(t, i, val)]
        else:  # if no data parameters, add "time" and "index" to the data dictionary
            try:
                self.data["time"].append(t)
                self.data["index"].append(i)
            except KeyError:
                self.data["time"] = [t]
                self.data["index"] = [i]

    def cleanup(self):
        """Saves data to a csv file as a pandas DataFrame.

        The output DataFrame has a single index, and a time column. Data values are stored in the columns, and are
        named source.param. This allows multiple workers to feed the same thread without causing namespace collisions.
        """
        if self.data:
            dfs = []
            try:  # if data dict has a "time" and "index" key, add these to the DataFrame
                t = self.data.pop("time")
                i = self.data.pop("index")
                df = pd.DataFrame(dict(time=t), index=i)
                dfs.append(df)
            except KeyError:
                t, i = None, None
            for param, data in self.data.items():
                t_param, i_param, vals = zip(*data)
                df_data = {param: vals}
                if not t:  # if data dict did not have "time" and "index" keys, take from first param instead
                    t = t_param
                    df_data["time"] = t
                df = pd.DataFrame(df_data, index=i_param)  # create df with param data and index
                dfs.append(df)
            # combine all data together into a single DataFrame and save as a csv
            df = pd.concat(dfs, axis=1)
            df.to_csv(self.path)


class TimestampedThread(Thread):
    """Thread for saving timestamped data.

    Parameters
    ----------
    path : str
        File path where data is to be saved.
    q : queue.Queue
        Queue that contains serialized timestamped data.

    Attributes
    ----------
    data : dict
        Dictionary where incoming data are stored.
    """

    def __init__(self, path, q, *args, **kwargs):
        super().__init__(path, q, *args, **kwargs)
        self.data = None

    def setup(self):
        """Initializes the data attribute."""
        self.data = {}

    def dump(self, source, t, data):
        """Sorts and places data into the data dictionary.

        Parameters
        ----------
        source : str
            The source (i.e. worker name) of the data.
        t : float
        data : dict
        """
        for param, val in data.items():
            k = ".".join([source, param])
            if k in self.data:
                self.data[k].append((t, val))
            else:
                self.data[k] = [(t, val)]

    def cleanup(self):
        """Saves data to a csv file as a pandas DataFrame."""
        if self.data:
            dfs = []
            for param, data in self.data.items():
                t, vals = zip(*data)
                df = pd.DataFrame({
                    "time": t,
                    param: vals
                })
                dfs.append(df)
            # combine all data together into a single DataFrame and save as a csv
            df = pd.concat(dfs, axis=0, ignore_index=True)
            df.sort_values(by=["time"], inplace=True)
            df.to_csv(self.path, index=False)


def saver(method):
    """Decorator that sends data to the appropriate saving method when recording."""
    def wrapper(obj, source, dtype, *args):
        if obj.recording:
            obj.save_methods[dtype](source, *args)
        method(obj, source, dtype, *args)
    return wrapper


class PipelineSaver:
    """Class for saving data from workers belonging to the same pipeline.

    This class receives incoming data from the pydra saver object with a call to its update method. Class contains
    various threads, queues and caches for storing and saving data.

    Parameters
    ----------
    name : str
        The name of the pipeline.
    members : list
        A list of worker object types that belong to the pipeline.

    Attributes
    ----------
    frame_q, indexed_q, timestamped_q : queue.Queue
        Queues data of different types for saving by different threads.
    frame : np.ndarray
        A copy of the last frame received by the pipeline.
    timestamps : deque
        A queue that stores timestamps of incoming frames. Used to compute an actual frame rate for data acquisition.
    data_cache : dict
        A dictionary containing a copy of data received for workers.
    fourcc : str
        Codec for video compression.
    """

    def __init__(self, name: str, members: list):
        self.name = name
        self.members = members
        # Queues
        self.frame_q = queue.Queue()
        self.indexed_q = queue.Queue()
        self.timestamped_q = queue.Queue()
        # Save methods
        self.recording = False
        self.save_methods = {
            "frame": self.save_frame,
            "indexed": self.save_indexed,
            "timestamped": self.save_timestamped
        }
        # Data handling
        self.frame = None
        self.timestamps = deque(maxlen=1000)
        self.data_cache = {}
        self.fourcc = "XVID"

    @property
    def frame_rate(self) -> float:
        """Returns the actual frame rate of data acquisition."""
        return len(self.timestamps) / (self.timestamps[-1] - self.timestamps[0])

    @property
    def frame_size(self) -> tuple:
        """Returns the (width, height) of the last frame received."""
        return self.frame.shape[:2][::-1]

    @property
    def is_color(self) -> bool:
        """Returns whether incoming frames are color."""
        return self.frame.ndim > 2

    @saver
    def update(self, source, dtype, *args):
        """Called by pydra saver object when new data are received from workers."""
        # create cache for storing all data from a given source
        if source not in self.data_cache:
            self.data_cache[source] = {
                "time": [],
                "index": [],
                "data": {},
                "timestamped": []
            }
        # parse arguments
        if dtype == "frame":
            t, i, frame = args
            self.timestamps.append(t)
            self.frame = frame
            data = {}
            self.data_cache[source]["frame"] = frame
        elif dtype == "indexed":
            t, i, data = args
        elif dtype == "timestamped":
            t, data = args
            self.data_cache[source]["timestamped"] = [(t, data)]
            return
        else:
            return
        # update indexed data in cache
        self.data_cache[source]["time"].append(t)
        self.data_cache[source]["index"].append(i)
        for key, val in data.items():
            try:
                self.data_cache[source]["data"][key].append(val)
            except KeyError:
                self.data_cache[source]["data"][key] = [val]

    def flush(self):
        data_cache = self.data_cache.copy()
        self.data_cache = {}
        return data_cache

    def save_frame(self, source, t, i, frame):
        """Parses frame data into appropriate queues for saving."""
        self.frame_q.put((source, frame))
        self.indexed_q.put((source, t, i, {}))

    def save_indexed(self, source, t, i, data):
        """Puts indexed data into appropriate queue for saving."""
        self.indexed_q.put((source, t, i, data))

    def save_timestamped(self, source, t, data):
        """Puts timestamped data into appropriate queue for saving."""
        self.timestamped_q.put((source, t, data))

    def start(self, directory, filename):
        """Starts threads for saving incoming data."""
        # Create filepath from directory and pipeline
        directory = Path(directory)
        if not directory.exists():
            directory.mkdir(parents=True)
        if self.name:
            filename = "_".join([filename, self.name])
        filepath = str(directory.joinpath(filename))
        # Frame thread
        if self.frame is not None:
            self.frame_thread = FrameThread(filepath + ".avi", self.frame_q, int(self.frame_rate), self.frame_size,
                                            self.fourcc, self.is_color)
            self.frame_thread.start()
        else:
            self.frame_thread = None
        # Indexed thread
        self.indexed_thread = IndexedThread(filepath + ".csv", self.indexed_q)
        self.indexed_thread.start()
        # Timestamped thread
        self.timestamped_thread = TimestampedThread(filepath + "_events.csv", self.timestamped_q)
        self.timestamped_thread.start()
        # Set recording to True
        self.recording = True

    def stop(self):
        """Terminates and joins saving threads."""
        # Send termination signal
        self.timestamped_q.put(b"")
        self.indexed_q.put(b"")
        self.frame_q.put(b"")
        # Join threads
        self.timestamped_thread.join()
        self.indexed_thread.join()
        if self.frame_thread:
            self.frame_thread.join()
        # Set recording to False
        self.recording = False
