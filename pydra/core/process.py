from .workers import WorkerConstructor
from multiprocessing import Process, Event
from multiprocessing.connection import Connection
import time


class PydraProcess(Process):

    def __init__(
            self,
            constructor: WorkerConstructor,
            exit_flag: Event,
            start_flag: Event,
            stop_flag: Event,
            finished_flag: Event,
            connection: Connection,
            *args, **kwargs
    ):
        """Pydra process class.

        Parameters
        ----------
        constructor : WorkerConstructor
            A WorkerConstructor object.
        exit_flag : Event
            Signal telling the main loop of the core when to exit.
        finished_flag : Event
            Signal sent by the core once it has finished.
        """
        super().__init__(*args, **kwargs)
        self.constructor = constructor  # worker constructor object
        self.exit_flag = exit_flag  # flag that tells process to exit
        self.start_flag = start_flag  # flag that tells process to begin the worker event loop
        self.stop_flag = stop_flag  # flag that tells the process to end the worker event loop
        self.finished_flag = finished_flag  # flag that informs other processes that the worker event loop as ended
        self.connection = connection  # connection from the main process to receive events
        self.worker = None

    def _recv(self):
        """Updates keyword arguments of the worker object."""
        if self.connection.poll():
            data = self.connection.recv()
            if isinstance(data, WorkerConstructor):
                handles = dict(((name, self.worker.__getattribute__(name)) for name in self.worker.handles))
                self.constructor = data
                self.constructor.kwargs.update(handles)
            elif isinstance(data, dict):
                self.constructor.update(**data)
            elif isinstance(data, tuple):
                self.constructor.update(*data)
            else:
                self.connection.send(False)
                return
            self.worker = self.constructor()
            self.connection.send(True)
        else:
            time.sleep(0.001)

    def run(self):
        """Code that runs when process is started."""
        self.worker = self.constructor()
        while not self.exit_flag.is_set():  # "event loop" runs as long as exit flag is not set
            self._recv()  # receive worker arguments from the main process
            if self.start_flag.is_set():  # check if start flag is set
                self.worker.setup()
                while not self.stop_flag.is_set():  # run the worker event loop until stop flag is set
                    self.worker._run()
                    self.worker._handle_events()
                self.worker.cleanup()  # cleanup worker
                self.worker._flush_events()  # flush any remaining events
                self.finished_flag.set()  # set the finished flag
