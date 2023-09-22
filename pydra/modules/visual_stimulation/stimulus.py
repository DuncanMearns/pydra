import importlib.util
import time


class ProtocolRunner:
    """Class for running protocols (i.e. lists of Stimulus objects).

    Attributes
    ----------
    stimulus_list : list
        List of Stimulus objects to be called sequentially.
    window
        Psychopy window for drawing stimuli.
    current_stimulus : Stimulus
        The current stimulus.
    """

    @classmethod
    def from_protocol(cls, window, filepath: str):
        """Creates a ProtocolRunner object from a Psychopy window and a file containing a stimulus list."""
        protocol_runner = cls(window)
        protocol_runner.load_protocol(filepath)
        return protocol_runner

    def __init__(self, window, stimulus_list: list = None):
        self.stimulus_list = stimulus_list or []
        self.set_window(window)
        self.current_stimulus = None
        self._current_idx = 0
        self._completed_stimuli = []
        self.running = False

    @property
    def running(self):
        return self._running

    @running.setter
    def running(self, val: bool):
        self._running = val

    def start(self, idx=0):
        """Initializes the stimulus list.

        Sets the starting index, resets all stimuli in the stimulus list and sets the running property to True.
        """
        self._current_idx = idx
        for stimulus in self.stimulus_list:
            stimulus.reset()
        try:
            self.current_stimulus = self.stimulus_list[self._current_idx]
            self._completed_stimuli = []
            self.running = True
        except IndexError:
            print("Cannot start protocol without stimulus list!")

    def __call__(self, *args, **kwargs):
        """Calls the current stimulus if the running property is True."""
        if self.running:
            ret = self.current_stimulus(*args, **kwargs)
            self.window.flip()
            if ret:
                self.next()
            return True
        return False

    def next(self):
        """Sets the next stimulus in the stimulus list as the current stimulus."""
        self._completed_stimuli.append(self.current_stimulus)
        self._current_idx += 1
        try:
            self.current_stimulus = self.stimulus_list[self._current_idx]
        except IndexError:
            self.current_stimulus = None
            self.running = False

    def stop(self):
        """Stops a running protocol. Flips the window and sets the running property to False."""
        self.window.flip()
        self.running = False

    def set_window(self, win=None):
        """Sets the window for drawing stimuli."""
        if win:
            self.window = win
        for stimulus in self.stimulus_list:
            stimulus.window = self.window

    def load_protocol(self, filepath):
        """Loads a stimulus list from a given file."""
        try:
            spec = importlib.util.spec_from_file_location("stimulus", filepath)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        except AttributeError:
            print("Path to stimulus not specified.")
            return
        except FileNotFoundError:
            print("Path to stimulus file does not exist.")
            return
        try:
            stimulus_list = mod.stimulus_list
            self.stimulus_list = list(stimulus_list)
        except AttributeError:
            print(f"{filepath} does not contain a `stimulus_list` variable.")
        except TypeError:
            print("`stimulus_list` must be a list of Stimulus objects")
        self.set_window()
        print(f"Stimulus loaded from: {filepath}")

    def logging_info(self):
        info = {}
        for stimulus in self.stimulus_list:
            logged = stimulus.log()
            if logged:
                info.update(logged)
        return info


class Stimulus:
    """Base class for creating stimuli.

    Attributes
    ----------
    window
        The Psychopy window where stimuli can be drawn.
    started : bool
        Property, True if the stimulus has started, otherwise False.
    finished : bool
        Property, True if a stimulus has finished running, other False.
    _exit_flag : bool (private)
        Returned on call. True is a stimulus has completed, otherwise False.

    Notes
    -----
    Stimulus objects are designed to be called repeatedly in a loop. Their behavior is dictated by a number of internal
    flags (public and private) that are stored as properties/attributes. The first time the object is called, the
    `on_start` method is executed once. Thereafter, the `update` method is run on each call until the finished flag is
    set to True. Once the finished flag is True, the next call of the object with execute the `on_stop` method once.
    Calling the object will return False as long as it is running. Once the finished flag is set and the `on_stop`
    method has returned, the object will return True, indicating the stimulus has completed successfully.

    The reset method can be used to reset the internal flags, allowing the stimulus to be run again.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.window = None
        self.started = False
        self.finished = False
        self._exit_flag = False

    def __call__(self, *args, **kwargs) -> bool:
        if not self._exit_flag:
            if self.finished:
                self.on_stop(*args, **kwargs)
                self._exit_flag = True
            elif self.started:
                self.update(*args, **kwargs)
            else:
                self.on_start(*args, **kwargs)
                self.started = True
        return self._exit_flag

    @property
    def window(self):
        return self._window

    @window.setter
    def window(self, win):
        self._window = win

    @property
    def started(self):
        return self._started

    @started.setter
    def started(self, val: bool):
        self._started = val

    @property
    def finished(self):
        return self._finished

    @finished.setter
    def finished(self, val: bool):
        self._finished = val

    def reset(self):
        self.started = False
        self.finished = False
        self._exit_flag = False

    def log(self):
        pass

    def on_start(self, *args, **kwargs):
        return

    def update(self, *args, **kwargs):
        return

    def on_stop(self, *args, **kwargs):
        return


class Wait(Stimulus):

    def __init__(self, t, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.t = t
        self.t0 = -1

    def on_start(self, *args, **kwargs):
        self.t0 = time.time()

    def update(self, *args, **kwargs):
        if time.time() - self.t0 >= self.t:
            self.finished = True
