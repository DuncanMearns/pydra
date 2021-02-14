import u3


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
