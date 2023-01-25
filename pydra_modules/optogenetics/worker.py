from pydra import Worker
from pydra.modules.labjack import LabJack
import time


class OptogeneticsWorker(LabJack, Worker):

    name = "optogenetics"
    gui_events = ("stimulation_on", "stimulation_off")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_callbacks["disconnect"] = self.stimulation_off
        self.laser_state = 0

    def stimulation_off(self, **kwargs):
        self.send_signal('DAC0', 0)
        self.laser_state = 0
        print("LASER OFF")
        t = time.time()
        self.send_timestamped(t, {"laser": 0})

    def stimulation_on(self, **kwargs):
        self.laser_state = 1
        self.send_signal('DAC0', 1.5)
        print("LASER ON")
        t = time.time()
        self.send_timestamped(t, {"laser": 1})

    def cleanup(self):
        self.stimulation_off()
