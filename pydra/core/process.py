from multiprocessing import Process


class PydraProcess(Process):
    """Class for running pydra objects in a separate process.

    The run method of PydraProcess calls the constructor for the worker class and then calls the run method of the
    newly created object.

    Parameters
    ----------
    worker_type : type
        Worker type (should be a subclass of PydraObject and ProcessMixIn).
    worker_args : iterable
        Arguments passed with star to the constructor of the worker pydra object.
    worker_kwargs : dict
        Keyword arguments passed with double star to the constructor of the worker pydra object.

    Attributes
    ----------
    worker : PydraObject
        An instance of a PydraObject class.
    """

    def __init__(self, worker_type, worker_args, worker_kwargs, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.worker_type = worker_type
        self.worker_args = worker_args
        self.worker_kwargs = worker_kwargs

    def run(self):
        self.worker = self.worker_type(*self.worker_args, **self.worker_kwargs)
        self.worker.run()


class ProcessMixIn:
    """Mix-in class for running pydra objects in a separate process.

    Provides such classes with a run method that is called after the object is instantiated in a separate process. Also
    provides a start classmethod that launches the object in a separate process.

    Attributes
    ----------
    exit_flag : int
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exit_flag = 0

    @classmethod
    def start(cls, *args, **kwargs):
        """Launches the object in a separate process. Parameters are the same as the constructor."""
        process = PydraProcess(cls, args, kwargs)
        process.start()
        return process

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
