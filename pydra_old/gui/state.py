class StateEnabled:

    state_enabled = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def idle(self):
        pass

    def live(self):
        pass

    def record(self):
        pass
