class Stimulus:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.window = None
        self.running = False

    @property
    def window(self):
        return self._window

    @window.setter
    def window(self, win):
        self._window = win

    @property
    def running(self):
        return self._running

    @running.setter
    def running(self, val: bool):
        self._running = val

    def create(self):
        return

    def update(self):
        return

    def destroy(self):
        return


class Wait(Stimulus):

    def __init__(self, t, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.t = t
