from multiprocessing import Process, Queue, Event
import queue


__all__ = ['MedusaWorker', 'MedusaProcess']


class MedusaWorker:
    """
    Abstract worker class for Medusa processes.

    Subclasses must implement a process method and may additionally implement a setup and cleanup method invoked at the
    beginning and end of the process run, respectively.
    """

    def __init__(self, **kwargs):
        super().__init__()
        self.events = []

    def setup(self):
        """Method called once when a process is spawned."""
        return

    def _run(self):
        """Method that is called within a MedusaProcess's main loop until the exit signal has been set. Must be
        overwritten in subclasses."""
        return

    def _handle_events(self):
        for event, func in self.events:
            if event.is_set():
                func()
                event.clear()
        return

    def cleanup(self):
        """Method called at the end of a process after the main loop has exited. After this method is called, the
        process's finished signal is set and the process ends."""
        return

    @staticmethod
    def _flush(q: Queue):
        """Can be used to flush queues after an exit signal has been received."""
        while True:
            try:
                obj = q.get_nowait()
                yield obj
            except queue.Empty:
                return


class MedusaProcess(Process):

    def __init__(self, worker_cls: type, exit_signal: Event, finished_signal: Event, worker_kwargs: dict = None):
        """Medusa process class.

        Parameters
        ----------
        worker_cls : MedusaWorker type
            Any MedusaWorker class.
        exit_signal : Event
            Signal telling the main loop of the process when to exit.
        finished_signal : Event
            Signal sent by the process once it has finished.
        worker_kwargs : dict
            Dictionary containing keyword arguments passed to the worker's __init__ method.
        """
        super().__init__()
        self.worker_cls = worker_cls
        self.worker_kwargs = {}
        if worker_kwargs is not None:
            self.worker_kwargs.update(worker_kwargs)
        self.exit_signal = exit_signal
        self.finished_signal = finished_signal
        self.worker = None

    def run(self):
        """Code that runs when process is started."""
        self.worker = self.worker_cls(**self.worker_kwargs)
        self.worker.setup()
        while not self.exit_signal.is_set():
            self.worker._run()
            self.worker._handle_events()
        self.worker.cleanup()
        self.finished_signal.set()
