"""
Module that allows for parallelization of pydra network.

Provides a Parallelized mixin class that allows PydraObjects to be run in separate threads or processes along with
functions and a factory class for spawning and running new processes.
"""
from __future__ import annotations

from .pydra_object import *
from .messaging import *
from multiprocessing import Process
from threading import Thread
import pickle
from typing import Tuple, Type, Union
from collections import namedtuple


__all__ = ("spawn_new", "Parallelized")


class Parallelized:
    """Mix-in class for running pydra objects in a separate process.

    Notes
    -----
    Provides classes with a run method that is called after the object is instantiated in a separate process.
    """

    name = ""
    subscriptions = ()
    pydra_error = namedtuple("PydraError", ("error", "message", "critical"))

    @classmethod
    def new_subscription(cls, worker: Union[Type[PydraObject], str]):
        if issubclass(worker, PydraObject):
            worker = worker.name
        subscriptions = list(cls.subscriptions)
        subscriptions.append(worker)
        cls.subscriptions = tuple(set(subscriptions))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exit_flag = 0
        self.is_connected = False
        self.errors = []

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
        self._handle_errors()
        while not self.exit_flag:
            self._process()
            self._handle_errors()
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

    def _handle_errors(self):
        while len(self.errors):
            error, message, critical = self.errors.pop(-1)
            self.raise_error(error, message, critical)
            # if critical:
            #     self.close()  # breaks the event loop

    def catch_error(self, error: Exception, message: str = "", critical: bool = False):
        self.errors.append(self.pydra_error(error, message, critical))

    @ERROR.SEND
    def raise_error(self, error: Exception, message: str, critical: bool = False):
        return error, message, critical


class PydraFactory:
    """Factory class that allows Workers and Savers to be created and run in separate processes.

    Parameters
    ----------
    name : str
        Name of the pydra object.
    bases : iterables of types
        The class to be instantiated in another process.
    subscriptions : tuple
        Subscriptions class attribute.
    """

    @classmethod
    def from_class(cls, worker_class: Type[Parallelized]) -> PydraFactory:
        return cls(worker_class.name, (worker_class,), worker_class.subscriptions)

    @classmethod
    def from_bases(cls, worker_class: Type[Parallelized]) -> PydraFactory:
        return cls(worker_class.name, worker_class.__bases__, worker_class.subscriptions)

    def __init__(self, name: str, bases: Tuple[Type], subscriptions: tuple):
        self.name = name
        self.bases = bases
        self.subscriptions = subscriptions

    def __call__(self, *args, **kwargs):
        """Calling the factory returns an instance of the associated class."""
        cls_type = PydraType(self.name, self.bases, {"name": self.name,
                                                     "subscriptions": self.subscriptions})
        return cls_type(*args, **kwargs)


def generate_factory(pydra_cls: Type[Parallelized]):
    for factory_method in [PydraFactory.from_class, PydraFactory.from_bases]:
        try:
            factory = factory_method(pydra_cls)
            pickle.dumps(factory)  # check pickleable
            return factory
        except pickle.PickleError:
            continue
    raise ValueError(f"Cannot pickle {pydra_cls}.")


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


def spawn_new(pydra_cls: Type[Parallelized], args, kwargs, as_thread=False) -> Union[Thread, Process]:
    """Runs a parallelized pydra object in another thread or process.

    Parameters
    ----------
    pydra_cls : Parallelized type
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
    factory = generate_factory(pydra_cls)
    if as_thread:
        runner = Thread
        name = f"Thread-{pydra_cls.name}"
    else:
        runner = Process
        name = f"Process-{pydra_cls.name}"
    new = runner(target=run_instance, args=(factory, args, kwargs), name=name)
    new.start()
    return new
