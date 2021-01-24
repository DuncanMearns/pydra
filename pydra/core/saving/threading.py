from ..messaging import *
from ..messaging.serializers import *
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
        frame : bytes
            A pickled numpy array.
        """
        frame = deserialize_array(frame)
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
        t : bytes
            Serialized timestamp (float).
        i : bytes
            Serialized index (int).
        data : bytes
            Serialized data (dict).
        """
        t, i, data = INDEXED.decode(t, i, data)   # deserialize data
        try:
            self.data[source]["time"].append(t)   # append timestamp
            self.data[source]["index"].append(i)  # append index
            if data:
                for key, val in data.items():
                    self.data[source]["data"][key].append(val)  # append data values (if they exist)
        except KeyError:  # create a new dictionary if data is received from a source for the first time
            self.data[source] = dict(time=[t], index=[i])
            if data:
                for key, val in data.items():
                    self.data[source]["data"] = {key: [val]}

    def cleanup(self):
        """Saves data to a csv file as a pandas DataFrame.

        The output DataFrame has a single index, and a timestamp column for each source that fed the thread during
        saving (denoted source_t). Data values are stored in columns, similarly prefixed with the source name. This
        allows multiple workers to feed the same saving thread without causing namespace collisions.
        """
        dfs = []
        for source, data in self.data.items():
            if "data" in data:
                df = pd.DataFrame(data["data"], index=data["index"])
                col_map = {}
                for col in df.columns:
                    col_map[col] = "_".join([source, col])
                df.rename(columns=col_map, inplace=True)
            else:
                df = pd.DataFrame(index=data["index"])
            df[source + "_t"] = data["time"]
            dfs.append(df)
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
        t : bytes
            Serialized timestamp (float).
        data : bytes
            Serialized data (dict).
        """
        t, data = TIMESTAMPED.decode(t, data)
        try:
            self.data[source]["time"].append(t)
            for key, val in data.items():
                self.data[source][key].append(val)
        except KeyError:
            self.data[source] = dict(time=[t])
            for key, val in data.items():
                self.data[source][key] = [val]

    def cleanup(self):
        """Not yet implemented."""
        return


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
        return deserialize_array(self.frame).shape[:2][::-1]

    @property
    def is_color(self) -> bool:
        """Returns whether incoming frames are color."""
        return deserialize_array(self.frame).ndim > 2

    def update(self, source, dtype, *args):
        """Called by pydra saver object when new data are received from workers."""
        t = deserialize_float(args[0])
        i = None
        if dtype == "frame":
            self.timestamps.append(t)
            i = deserialize_int(args[1])
            self.frame = args[2]
            data = None
        elif dtype == "indexed":
            i = deserialize_int(args[1])
            data = deserialize_dict(args[2])
        elif dtype == "timestamped":
            data = deserialize_dict(args[1])
        else:
            return
        if source in self.data_cache:
            self.data_cache[source]["time"].append(t)
            if i is not None:
                self.data_cache[source]["index"].append(i)
            if data:
                for key, val in data.items():
                    self.data_cache[source]["data"][key].append(val)
        else:
            self.data_cache[source] = {}
            self.data_cache[source]["time"] = [t]
            if i is not None:
                self.data_cache[source]["index"] = [i]
                if data:
                    self.data_cache[source]["data"] = {}
                    for key, val in data.items():
                        self.data_cache[source]["data"][key] = [val]

    def flush(self):
        serialized = serialize_dict(self.data_cache)
        self.data_cache = {}
        return serialized

    def save_frame(self, source, t, i, frame):
        """Parses frame data into appropriate queues for saving."""
        self.frame_q.put((source, frame))
        self.indexed_q.put((source, t, i, "null".encode("utf-8")))

    def save_indexed(self, source, t, i, data):
        """Puts indexed data into appropriate queue for saving."""
        self.indexed_q.put((source, t, i, data))

    def save_timestamped(self, source, t, data):
        """Puts timestamped data into appropriate queue for saving."""
        self.timestamped_q.put((source, t, data))

    def start(self, directory, filename):
        """Starts threads for saving incoming data."""
        # Base name
        directory = Path(directory)
        if not directory.exists():
            directory.mkdir(parents=True)
        filename = str(directory.joinpath(filename + self.name))
        # Frame thread
        self.frame_thread = FrameThread(filename + ".avi", self.frame_q, int(self.frame_rate), self.frame_size,
                                        self.fourcc, self.is_color)
        self.frame_thread.start()
        # Indexed thread
        self.indexed_thread = IndexedThread(filename + ".csv", self.indexed_q)
        self.indexed_thread.start()
        # Timestamped thread
        self.timestamped_thread = TimestampedThread(filename + "_events.csv", self.timestamped_q)
        self.timestamped_thread.start()

    def stop(self):
        """Terminates and joins saving threads."""
        # Send termination signal
        self.timestamped_q.put(b"")
        self.indexed_q.put(b"")
        self.frame_q.put(b"")
        # Join threads
        self.timestamped_thread.join()
        self.indexed_thread.join()
        self.frame_thread.join()
