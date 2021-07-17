import threading
import queue
import cv2
import numpy as np
import pandas as pd
import h5py


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
        self.to_save = None

    def setup(self):
        """Initializes the data attribute."""
        self.data = {}

    def dump(self, source, t, i, data, a=()):
        """Sorts and places data into the data dictionary.

        Parameters
        ----------
        source : str
            The source (i.e. worker name) of the data.
        t : float
        i : int
        data : dict
        a : np.ndarray (optional)
        """
        try:
            d = self.data[source]
        except KeyError:
            self.data[source] = {}
            d = self.data[source]
        try:
            d["index"].append((t, i))
        except KeyError:
            d["index"] = [(t, i)]
        for param, val in data.items():  # add parameter values to the data dictionary with key source.param
            try:
                d[param].append(val)
            except KeyError:
                d[param] = [val]
        if len(a):
            try:
                d["array"].append(a)
            except KeyError:
                d["array"] = [a]

    def cleanup(self):
        """Saves data to a csv file as a pandas DataFrame.

        The output DataFrame has a single index, and a time column. Data values are stored in the columns, and are
        named source.param. This allows multiple workers to feed the same thread without causing namespace collisions.
        """
        self.to_save = {}
        if self.data:
            path = self.path[:-3] + "hdf5"
            with h5py.File(path, "w") as f:
                for worker, worker_data in self.data.items():
                    worker_dset = f.create_group(worker)
                    for param, vals in worker_data.items():
                        worker_dset.create_dataset(param, data=np.array(vals))


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
