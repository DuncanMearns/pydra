from multiprocessing import Process
import time


class _BaseProcess(Process):

    def __init__(self):
        super().__init__()

    def setup(self):
        return

    def cleanup(self):
        return


class AcquisitionProcess(_BaseProcess):

    def __init__(self, q_out, exit_flag):
        super().__init__()
        self.q_out = q_out
        self.exit_flag = exit_flag

    def acquire(self):
        return

    def run(self):
        self.setup()
        while not self.exit_flag.is_set():
            result = self.acquire()
            self.q_out.put(result)
        print('acquisition ended')
        print(self.q_out.qsize())
        self.q_out.close()
        self.cleanup()


class TrackingProcess(_BaseProcess):

    def __init__(self, q_in, q_out, exit_flag):
        super().__init__()
        self.q_in = q_in
        self.q_out = q_out
        self.exit_flag = exit_flag

    def process(self, *args):
        return

    def run(self):
        self.setup()
        while not self.exit_flag.is_set():
            input_from_q = self.q_in.get()
            result = self.process(input_from_q)
            self.q_out.put(result)
        print('tracking ended')
        print(self.q_out.qsize())
        self.q_out.close()
        self.cleanup()


class SavingProcess(_BaseProcess):

    def __init__(self, q_in, exit_flag):
        super().__init__()
        self.q_in = q_in
        self.exit_flag = exit_flag

    def dump(self, *args):
        return

    def run(self):
        self.setup()
        while not self.exit_flag.is_set():
            input_from_q = self.q_in.get()
            self.dump(input_from_q)
        print('saving ended')
        self.cleanup()
