from ..core import ProtocolWorker
from psychopy import visual
import time


class VisualStimulation(ProtocolWorker):

    def __init__(self, stimuli: list, window_params: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Window
        self.window_params = window_params
        self.window = visual.Window(**self.window_params)
        # Stimuli
        self.stimuli = stimuli
        self.n = 0
        self.current = None
        self.finished = False

    def setup(self):
        self.finished = False
        self.n = 0
        stimulus, kw = self.stimuli[self.n]
        self.current = stimulus(window=self.window, **kw)

    def _run(self):
        if not self.current.finished:  # update the current stimulus and draw to the window
            self.current.update()
            self.window.flip()
        else:  # current stimulus has ended
            if self.finished:  # if all stimuli have finished, do nothing
                time.sleep(0.1)
            else:  # start the next stimulus
                self.n += 1
                if self.n < len(self.stimuli):
                    stimulus, kw = self.stimuli[self.n]
                    self.current = stimulus(window=self.window, **kw)
                else:  # if all stimuli have finished, set the protocol finished flag to True and inform main process
                    self.finished = True
                    self.sender.put(True)

    # def cleanup(self):
    #     self.window.close()
