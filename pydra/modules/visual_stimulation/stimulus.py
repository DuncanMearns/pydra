class Stimulus:

    def __init__(self, window):
        super().__init__()
        self.window = window
        self._running = False

    @property
    def window(self):
        return self._window

    @window.setter
    def window(self, win):
        self._window = win

    def start(self):
        return

    def update(self):
        return

    def stop(self):
        return

    def is_running(self):
        return self._running

    def set_running(self, a: bool):
        self._running = a
