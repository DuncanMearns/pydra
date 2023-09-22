from pydra.modules.visual_stimulation import Stimulus, Wait
import numpy as np
import time
from PIL import Image
from psychopy import visual, monitors


# OKR stimulus.
# Trying to induce saccadic eye movements on Theia

# 20230628. ~1cm width? 0.02 cycles per degree. 100% black/white contrast. 6 rounds per minute?
# Presented from the side.


class RandomMultiStim(Stimulus):
    """Your stimulus class that randomly shows a number of stimuli.
    Inherit this class into another that has the create_stimulus_list function."""

    def __init__(self, isi, duration, n_presentations=None, total_duration=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_idx = None
        self.stimulus_indices = None
        self.wait_stimulus = None
        self.current_stimulus = None
        self.list_of_stimuli = None
        self.isi = isi
        self.duration = duration
        self._n_presentations = n_presentations  # number of times each stimulus is displayed
        self._total_duration = total_duration

        self.on_start()

    @property
    def n_presentations(self):
        if self._n_presentations:
            return self._n_presentations
        elif self._total_duration:
            stim_time = self.duration + self.isi
            n_presentations_calc = self._total_duration // stim_time
            return n_presentations_calc
        else:
            raise ValueError("n_presentations or total_duration must be specified.")

    @property
    def total_duration(self):
        return self.n_presentations * (self.duration + self.isi)

    @property
    def show_idx(self):
        try:
            return self.stimulus_indices[self.current_idx]
        except IndexError:
            return None

    def start_message(self):
        return f"Showing stimulus {self.current_idx} at {self.current_stimulus.position}"

    def on_start(self):
        # create our rect stimuli with each respective location
        self.list_of_stimuli = self.create_stimulus_list()
        for stimulus in self.list_of_stimuli:
            stimulus.window = self.window

        # Create wait stimulus
        self.wait_stimulus = Wait(self.isi)

        # Randomize stimulus presentation order
        stimulus_indices = self.n_presentations
        self.stimulus_indices = np.random.permutation(stimulus_indices)
        self.current_idx = 0

        self.current_stimulus = self.list_of_stimuli[self.show_idx]  # make the current stimulus the rect stimulus
        print("Expected duration:", self.total_duration, "seconds")
        print(self.start_message(), end=" ")

    def update(self):
        is_stim_finished = self.current_stimulus()  # calling the stimulus updates it, ret is whether stimulus has finished
        if is_stim_finished:
            self.current_stimulus.reset()  # reset so it can be used again later
            if self.current_stimulus in self.list_of_stimuli:
                print(f"finished!")
                self.current_idx += 1  # increment the stimulus number
                self.current_stimulus = self.wait_stimulus  # set the current stimulus to wait
                print("Waiting...")
            else:
                if self.show_idx is not None:
                    self.current_stimulus = self.list_of_stimuli[self.show_idx]
                    print(self.start_message(), end=" ")
                else:  # run out of stimuli
                    self.finished = True

    def on_stop(self):
        print("All stimuli finished!")

    def log(self) -> dict:
        if self.current_stimulus:
            return self.current_stimulus.log()


class GratingStimulus(Stimulus):
    """ This is the grating that forms the base of the OKR stimulus
    Creates the grating and draws it at a certain position. """

    def __init__(self, sf, contrast, isi, duration, n_presentations, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sf = sf
        self.contrast = contrast
        self.isi = isi
        self.duration = duration
        self.position = [0, 0]
        self.color = [0, 0, 0]

        self.total_duration = n_presentations * self.duration + n_presentations * self.isi

        self.okr_stimulus = None
        self.t_end = None
        self._logged = False

    def on_start(self):
        self.okr_stimulus = visual.GratingStim(win=self.window,
                                               tex='sin',
                                               sf=self.sf,
                                               units='norm',  # if 'norm', sf units in cycles per stimulus
                                               size=my_monitor.getSizePix(),  # fill the screen
                                               pos=self.position,
                                               interpolate=True,
                                               color=self.color,
                                               ori=0.0,
                                               phase=(0.0, 0.0))

        self.okr_stimulus.setAutoDraw(True)
        self.t_end = time.time() + self.total_duration

    def update(self):
        self.okr_stimulus.draw()
        t = time.time()
        if t >= self.t_end:
            self.finished = True
            return

    def on_stop(self):
        self.okr_stimulus.pos = [0, 0]

    def reset(self):
        super().reset()
        self._logged = False

    def log(self) -> dict:
        if not self._logged:
            self._logged = True
            return {"position": self.okr_stimulus.pos, "stimulus": "okr"}


class OKRStimulus(GratingStimulus):

    def __init__(self, sf, contrast, isi, duration, n_presentations, *args, **kwargs):
        super().__init__(sf, contrast, isi, duration, n_presentations, *args, **kwargs)
        """Object for OKR stimulus, one round. Takes the GratingStimulus and drifts it. """
        self.sf = sf
        self.contrast = contrast
        self.isi = isi
        self.duration = duration

    def on_start(self):
        super().on_start()
        t = time.time()
        self.t_okr = t + self.duration

        self.okr_stimulus.draw()

    def update(self):
        """at every update, check where in the stim paradigm you are, act accordingly"""
        # set the next xy position
        while time.time() <= self.t_okr:
            self.okr_stimulus.setPhase(0.01, '+')
        super().update()

    def reset(self):
        super().reset()
        self.okr_stimulus.setAutoDraw(False)
        self.window.flip()

    def log(self) -> dict:
        return {"stimulus": "okr"}


class OKRs(RandomMultiStim):
    """Class that defines the stimulus list. In this case PseudoSaccade.
    Inhereits from RandomMultiStim that present the stimulus in create_stimulus_list randomly for n_presentations"""

    def __init__(self, sf, contrast, isi, duration, n_presentations, *args, **kwargs):
        super().__init__(isi, duration, n_presentations, *args, **kwargs)
        self.sf = sf
        self.contrast = contrast

    def create_stimulus_list(self):
        return [OKRStimulus(sf, contrast, isi, duration, n_presentations)]


my_monitor = monitors.Monitor(u'Lisa_Monitor')
screen_size = my_monitor.getSizePix()
units = 'degFlat'

# okr stimulus parameters
sf = 0.02  # cycles per degrees
contrast = 100  # percent

# Parameters that do change for testing
isi = 10  # At least 30 for experiments
duration = 5

n_presentations = 10

# this is imported and run by Pydra
stimulus_list = [OKRs(sf, contrast, isi, duration, n_presentations)]

if __name__ == "__main__":
    # monitor setup
    bg_color = (-1, -1, -1)

    # window
    window_params = dict(size=screen_size,
                         fullscr=False,
                         units=units,
                         color=bg_color,
                         allowGUI=True,
                         allowStencil=False,
                         monitor=my_monitor,
                         colorSpace=u'rgb',
                         blendMode=u'avg',
                         useFBO=True,
                         screen=0)
    win = visual.Window(**window_params)

    for stim in stimulus_list:
        stim.window = win

    idx = 0
    while True:
        try:
            ret = stimulus_list[idx]()
            win.flip()
            Wait(isi)
            if ret:
                idx += 1
        except IndexError:
            break
    print("DONE!")
