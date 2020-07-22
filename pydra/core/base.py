from multiprocessing import Process, Queue, Event, Pipe
import queue
import time


__all__ = ['Worker', 'PydraProcess']


class Worker:
    """
    Abstract worker class for Medusa core.

    Subclasses must implement a core method and may additionally implement a setup and cleanup method invoked at the
    beginning and end of the core run, respectively.
    """

    def __init__(self, **kwargs):
        self.events = []

    @classmethod
    def make(cls, **kwargs):
        return WorkerConstructor(cls, **kwargs)

    def setup(self):
        """Method called once when a core is spawned."""
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
        """Method called at the end of a core after the main loop has exited. After this method is called, the
        core's finished signal is set and the core ends."""
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


class WorkerConstructor:

    def __init__(self, worker, **kwargs):
        self.worker = worker
        self.kwargs = kwargs

    def update(self, *args, **kwargs):
        for key, value in args:
            self.kwargs[key] = value
        self.kwargs.update(**kwargs)

    def __call__(self, *args, **kwargs):
        return self.worker(**self.kwargs)


class Sender:

    def __init__(self, conn, flag):
        self.conn = conn
        self.flag = flag

    def send(self, *args, worker=None, **kwargs):
        if worker:
            constructor = worker.make(**kwargs)
            self.conn.send(constructor)
        elif len(args):
            self.conn.send(args)
        elif len(kwargs):
            self.conn.send(kwargs)
        else:
            return
        self.flag.set()


class Receiver:

    def __init__(self, conn, flag):
        self.conn = conn
        self.flag = flag

    def recv(self):
        if self.flag.is_set():
            message = self.conn.recv()
            self.flag.clear()
            return message
        else:
            return None


def pipe():
    flag = Event()
    conn1, conn2 = Pipe(duplex=False)
    receiver = Receiver(conn1, flag)
    sender = Sender(conn2, flag)
    return sender, receiver


class PydraProcess(Process):

    def __init__(
            self,
            constructor: WorkerConstructor,
            exit_flag: Event,
            start_flag: Event,
            stop_flag: Event,
            finished_flag: Event,
            connection: Receiver
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
        super().__init__()
        self.constructor = constructor  # worker constructor object
        self.exit_flag = exit_flag  # flag that tells process to exit
        self.start_flag = start_flag  # flag that tells process to begin the worker event loop
        self.stop_flag = stop_flag  # flag that tells the process to end the worker event loop
        self.finished_flag = finished_flag  # flag that informs other processes that the worker event loop as ended
        self.connection = connection  # connection to main process
        self.worker = None

    def _recv(self):
        """Updates keyword arguments of the worker object."""
        message = self.connection.recv()
        if message:
            if isinstance(message, WorkerConstructor):
                self.constructor = message
            elif isinstance(message, dict):
                self.constructor.update(**message)
            elif isinstance(message, tuple):
                self.constructor.update(*message)
            self.worker = self.constructor()
            self.wait_flag.clear()
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
                self.finished_flag.set()  # set the finished flag
