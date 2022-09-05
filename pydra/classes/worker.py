from .._base import *
from ..messaging import *
from ..utils.state import state_descriptor

from multiprocessing import Process
from threading import Thread
import typing
import os


__all__ = ("Worker", "Acquisition", "Saver", "spawn_new", "WorkerFactory")


class Parallelized:
    """Mix-in class for running pydra objects in a separate process.

    Provides such classes with a run method that is called after the object is instantiated in a separate process. Also
    provides a start classmethod that launches the object in a separate process.

    Attributes
    ----------
    exit_flag : int
    """

    name = ""
    subscriptions = ()
    connections = {}

    @classmethod
    def new_subscription(cls, worker: typing.Union[type(PydraObject), str]):
        if issubclass(worker, PydraObject):
            worker = worker.name
        subscriptions = list(cls.subscriptions)
        subscriptions.append(worker)
        cls.subscriptions = tuple(set(subscriptions))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exit_flag = 0

    def close(self):
        """Sets the exit_flag, causing process to terminate."""
        self.exit_flag = 1

    def setup(self):
        """Called once as soon as the object is created in a separate process."""
        return

    def _process(self):
        """Called repeatedly in a while loop for as long as the exit_flag is not set."""
        return

    def cleanup(self):
        """Called immediately before process terminates."""
        return

    def run(self):
        """Calls setup, and then enters an endless loop that calls the _process method for as long as the exit_flag is
        not set."""
        self.setup()
        while not self.exit_flag:
            self._process()
        self.cleanup()

    def exit(self, *args, **kwargs):
        """Sets the exit_flag when EXIT signal is received, causing process to terminate."""
        self.close()

    def _test_connection(self, **kwargs):
        """Called by the 'test_connection' event. Informs pydra that 0MQ connections have been established and worker is
        receiving messages."""
        self.connected()

    @CONNECTION
    def connected(self):
        return True,


class Worker(Parallelized, PydraPublisher, PydraSubscriber):
    """Base worker class.

    Attributes
    ----------
    name : str
        A unique string identifying the worker. Must be specified in all subclasses.
    subscriptions : tuple
        Names of other workers in the network from which this one can receive pydra messages.
    """

    gui_events = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _process(self):
        """Handles all messages received over network from ZeroMQ."""
        self.poll()


class Acquisition(Worker):
    """Base worker class for acquiring data. Implements an independent acquire method after checking for messages."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _process(self):
        """Checks for messages received over network from ZeroMQ, then calls the acquire method."""
        super()._process()
        self.acquire()

    def acquire(self):
        return


recording_state = state_descriptor.new_type("recording_state")


class Saver(Parallelized, PydraPublisher, PydraSubscriber):
    """Base saver class.

    Attributes
    ----------
    workers : tuple
        Tuple of worker names (str) that saver listens to.
    args : tuple
        Passed to *args when saver instantiated.
    kwargs : dict
        Passed to **kwargs when saver instantiated.
    _connections : dict
        Private attribute containing zmq connections. Must be set before instantiation.
    """

    # States
    idle = recording_state(0)
    recording = recording_state(1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.idle()

    def setup(self):
        """Sends a connected signal."""
        self.connected()

    def _process(self):
        self.poll()

    @staticmethod
    def new_file(directory, filename, ext=""):
        if ext:
            filename = ".".join((filename, ext))
        f = os.path.join(directory, filename)
        return f

    def start_recording(self, directory=None, filename=None, idx=0, **kwargs):
        self.recording()

    def stop_recording(self, **kwargs):
        self.idle()


class WorkerFactory:
    """Factory class that allows Workers and Savers to be created and run in separate processes.

    Parameters
    ----------
    name : str
        Name of the worker.
    worker_subclass : type[Parallelized]
        The class to be instantiated in another process.
    subscriptions : tuple
        Subscriptions class attribute.
    connections : dict
        Connections class attribute.
    """

    @classmethod
    def from_worker(cls, worker_subclass: typing.Type[Parallelized]):
        return cls(worker_subclass.name, worker_subclass, worker_subclass.subscriptions, worker_subclass.connections)

    def __init__(self, name: str, worker_subclass: typing.Type[Parallelized], subscriptions: tuple, connections: dict):
        self.name = name
        self.worker_subclass = worker_subclass
        self.subscriptions = subscriptions
        self.connections = connections

    def __call__(self, *args, **kwargs):
        """Calling the factory returns an instance of the worker_subclass."""
        cls_type = PydraType(self.name, (self.worker_subclass,), {"name": self.name,
                                                                  "subscriptions": self.subscriptions,
                                                                  "connections": self.connections})
        return cls_type(*args, **kwargs)


def run_worker(worker_factory: WorkerFactory, args: tuple, kwargs: dict) -> None:
    """Function for running parallelized pydra objects.

    Parameters
    ----------
    worker_factory : WorkerFactory
        A WorkerFactory instance for creating the worker.
    args : tuple
        Passed with * to instantiate the worker.
    kwargs : dict
        Passed with ** to instantiate the worker.
    """
    connections = worker_factory.connections
    kwargs.update(connections)
    worker = worker_factory(*args, **kwargs)
    worker.run()


def spawn_new(worker_factory, worker_args, worker_kwargs, as_thread=False) -> typing.Union[Thread, Process]:
    """Runs a parallelized pydra object in another thread or process.

    Parameters
    ----------
    worker_factory : WorkerFactory
        A WorkerFactory instance for creating the worker.
    worker_args : tuple
        Passed with * to instantiate the worker.
    worker_kwargs : dict
        Passed with ** to instantiate the worker.
    as_thread : bool
        If False (default), spawns worker in a separate process. If True, spawns a thread instead.

    Returns
    -------
    new : Union[Thread, Process]
        The new process or thread running the worker.
    """
    if as_thread:
        runner = Thread
        name = f"Thread-{worker_factory.name}"
    else:
        runner = Process
        name = f"Process-{worker_factory.name}"
    args = (worker_factory, worker_args, worker_kwargs)
    new = runner(target=run_worker, args=args,  name=name)
    new.start()
    return new
