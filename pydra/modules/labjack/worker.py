from pydra.core import Worker
import u3
import time


class LabJack:

    registers = {'DAC0': 5000,
                 'DAC1': 5002}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def connect(self, **kwargs):
        print('Connecting to labjack...', end=' ')
        self.u = u3.U3()
        for reg, addr in self.registers.items():
            self.u.writeRegister(addr, 0)
        print('done!\n')

    def send_signal(self, register, val):
        try:
            self.u.writeRegister(self.registers[register], val)
        except KeyError:
            raise Warning(f'{register} if not a valid DAC register (valid registers are: '
                          f'{[key for key in self.registers.keys()]}).')


class OptogeneticsWorker(LabJack, Worker):

    name = "optogenetics"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events["connect"] = self.connect
        self.events["disconnect"] = self.stimulation_off
        self.events["stimulation_on"] = self.stimulation_on
        self.events["stimulation_off"] = self.stimulation_off
        self.laser_state = 0

    def stimulation_off(self, **kwargs):
        self.send_signal('DAC0', 0)
        self.laser_state = 0
        print("LASER OFF")
        t = time.time()
        self.send_timestamped(t, {"laser": 0})

    def stimulation_on(self, **kwargs):
        self.laser_state = 1
        self.send_signal('DAC0', 3)
        print("LASER ON")
        t = time.time()
        self.send_timestamped(t, {"laser": 1})

    def cleanup(self):
        self.stimulation_off()
