"""Module for setting up Pydra. Handles different setup states and ensures each process/thread is connected."""
import time
from .state import state_descriptor


setup_state = state_descriptor.new_type("setup_state")


class SetupStateMachine:

    not_connected = setup_state(0)
    connecting = setup_state(1)
    finished = setup_state(2)

    def __init__(self, pydra):
        self.pydra = pydra
        self.t0 = 0
        self.module_idx = 0
        self.module_name = ""
        self.not_connected()

    def update(self):
        if self.not_connected:
            self.start_backend()
        if self.connecting:
            self.wait()

    def start_backend(self):
        print("Connecting to backend...")
        self.t0 = time.time()
        self.pydra.start_backend()
        self.module_name = "backend"
        self.connecting()

    def wait(self):
        connected, t = self.get_connected()
        if connected:
            print(f"{self.module_name} connected in {t - self.t0:.2f} seconds.\n")
            self.start_worker()
            return
        self.pydra.send_event("_test_connection")

    def start_worker(self):
        exists, name = self.pydra.load_module(self.module_idx)
        if exists:
            self.t0 = time.time()
            self.module_name = name
            self.module_idx += 1
            print(f"Connecting to {self.module_name}...")
            return
        self.finished()
        print("All modules connected.\n")

    def get_connected(self):
        return self.pydra._connection_times.get(self.module_name, (False, 0))
