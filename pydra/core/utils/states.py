"""Module for setting up Pydra. Handles different setup states and ensures each process/thread is connected."""
import time


class SetupState:
    connections = {}

    def __init__(self, idx, pydra, process_name, t0):
        self.idx = idx
        self.pydra = pydra
        self.process_name = process_name
        self.t0 = t0

    def __call__(self):
        return self

    def get_connected(self):
        return self.connections.get(self.process_name, (False, 0))

    def __str__(self):
        connected, t = self.get_connected()
        if connected:
            return f"{self.process_name} connected in {t - self.t0:.2f} seconds."
        else:
            return f"connecting to {self.process_name}..."

    def __repr__(self):
        return f"{type(self)}({self.idx}, {self.pydra}, {self.process_name}, {self.t0})"

    def next(self):
        return self

    def finished(self):
        return SetupFinished(self.pydra)


class NotConnected(SetupState):

    def __init__(self, pydra):
        super().__init__(-1, pydra, "backend", time.time())

    def __call__(self):
        self.pydra.start_backend()
        return self.next()

    def next(self):
        return Connecting(-1, self.pydra, "backend", time.time())


class StartWorker(SetupState):

    def __call__(self):
        exists, name = self.pydra.load_module(self.idx)
        if exists:
            self.process_name = name
            return self.next()
        return self.finished()

    def next(self):
        return Connecting(self.idx, self.pydra, self.process_name, time.time())


class Connecting(SetupState):

    def __call__(self):
        if self.get_connected()[0]:
            print(self)
            return self.next()
        self.pydra.send_event("_test_connection")
        return self

    def next(self):
        next_idx = self.idx + 1
        return StartWorker(next_idx, self.pydra, None, time.time())


class SetupFinished(SetupState):

    def __init__(self, pydra):
        super().__init__(-1, pydra, "pydra", time.time())

    def __str__(self):
        return "All modules connected."
