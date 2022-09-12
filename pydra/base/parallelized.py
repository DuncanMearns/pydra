"""
Module that allows for parallelization of pydra network.

Provides a Parallelized mixin class that allows PydraObjects to be run in separate threads or processes along with
functions and a factory class for spawning and running new processes.
"""
from __future__ import annotations

from ..base import *
from multiprocessing import Process
from threading import Thread
import typing


__all__ = ("PydraFactory", "spawn_new", "Parallelized")


class Parallelized:
    """Mix-in class for running pydra objects in a separate process.

    Notes
    -----
    Provides classes with a run method that is called after the object is instantiated in a separate process.
    """

    name = ""
    subscriptions = ()

    @classmethod
    def new_subscription(cls, worker: typing.Union[typing.Type[PydraObject], str]):
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

    @CONNECTION.SEND
    def connected(self):
        return ()

    @ERROR.SEND
    def raise_error(self, error: Exception, message: str):
        return error, message


class PydraFactory:
    """Factory class that allows Workers and Savers to be created and run in separate processes.

    Parameters
    ----------
    name : str
        Name of the pydra object.
    worker_class : type[Parallelized]
        The class to be instantiated in another process.
    subscriptions : tuple
        Subscriptions class attribute.
    """

    @classmethod
    def from_class(cls, worker_class: typing.Type[Parallelized]) -> PydraFactory:
        return cls(worker_class.name, worker_class, worker_class.subscriptions)

    def __init__(self, name: str, worker_class: typing.Type[Parallelized], subscriptions: tuple):
        self.name = name
        self.worker_subclass = worker_class
        self.subscriptions = subscriptions

    def __call__(self, *args, **kwargs):
        """Calling the factory returns an instance of the associated class."""
        cls_type = PydraType(self.name, (self.worker_subclass,), {"name": self.name,
                                                                  "subscriptions": self.subscriptions})
        return cls_type(*args, **kwargs)


def run_instance(pydra_factory: PydraFactory, args: tuple, kwargs: dict) -> None:
    """Function for running parallelized pydra instances.

    Parameters
    ----------
    pydra_factory : PydraFactory
        A WorkerFactory instance for creating the worker.
    args : tuple
        Passed with * to instantiate the pydra object.
    kwargs : dict
        Passed with ** to instantiate the pydra object.
    """
    pydra_instance = pydra_factory(*args, **kwargs)
    pydra_instance.run()


def spawn_new(pydra_factory, args, kwargs, as_thread=False) -> typing.Union[Thread, Process]:
    """Runs a parallelized pydra object in another thread or process.

    Parameters
    ----------
    pydra_factory : PydraFactory
        A PydraFactory instance for creating the pydra instance.
    args : tuple
        Passed with * to instantiate the worker.
    kwargs : dict
        Passed with ** to instantiate the worker.
    as_thread : bool
        If False (default), spawns worker in a separate process. If True, spawns a thread instead.

    Returns
    -------
    Thread or Process
        The new process or thread running the worker.
    """
    if as_thread:
        runner = Thread
        name = f"Thread-{pydra_factory.name}"
    else:
        runner = Process
        name = f"Process-{pydra_factory.name}"
    args = (pydra_factory, args, kwargs)
    new = runner(target=run_instance, args=args, name=name)
    new.start()
    return new
