from pydra.modules.visual_stimulation import Stimulus, Wait
import numpy as np
import time
from PIL import Image
from psychopy import visual, monitors


# Pseudo-saccade stimulus
# When looking at the spontaneous saccades Lisa has recorded,
# The average saccade duration is 0.3 seconds
# The average amplitude is 23.4 degrees
# The average velocity is ~78 degrees/sec
# Based on these parameters, Lisa has tried to create a pseudo-saccade stimulus, that mimicks what the fish would
# see when it's performing a spontaneous saccade.

# Right now, this happens.
# A Pseudosaccades stimulus list is created. Which is actually just a RandomMultiRect stimulus list. Which is Actually
# just a MovingRect stimulus list. Wow, great coding.
# The MovingRect creates a rectangular stimulus at certain width and height, at a specfiic location.
# This should cover the entire screen. I want this stimulus to move back and forth. The same amplitude.
# So, present wait, move a bit left, wait, move a bit right, wait, etc, etc.
# MovingRect stim should have grating with certain spatial frequency.


class RandomMultiStim(Stimulus):
    """Your stimulus class that randomly shows a number of stimuli.
    Inherit this class into another that has the create_stimulus_list function."""

    def __init__(self, locations, isi, duration, n_presentations=None, n_non_stimulus=None,
                 total_duration=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_idx = None
        self.stimulus_indices = None
        self.wait_stimulus = None
        self.current_stimulus = None
        self.list_of_stimuli = None
        self.locations = locations
        self.isi = isi
        self.duration = duration
        self._n_presentations = n_presentations  # number of times each stimulus is displayed
        self._n_non_stimulus = n_non_stimulus  # number of non stimulus trials
        self._total_duration = total_duration

    @property
    def n_presentations(self):
        if self._n_presentations:
            return self._n_presentations + self._n_non_stimulus
        elif self._total_duration:
            stim_time = self.duration + self.isi
            n_presentations_calc = self._total_duration // stim_time
            return n_presentations_calc
        else:
            raise ValueError("n_presentations or total_duration must be specified.")

    @property
    def total_duration(self):
        return self.n_presentations * len(self.locations) * (self.duration + self.isi)

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
        stimulus_indices = list(range(len(self.locations))) * self.n_presentations
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


class WholeFieldStimulus(Stimulus):
    """
    For showing a wholefield stimulus. In a Rectangular shape. Width and height should
    `on_start` is called when stimulus starts
    then `update` is called until `self.finished` flag is set to True
    then `on_stop` is called
    """

    def __init__(self, width: float, height: float, pos: tuple, duration: float, isi, sf, contrast, stimtype,
                 color: tuple = (1, 1, 1), *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.stimtype = stimtype
        self.wholefield_stimulus = None
        self.t_end = None
        self.width = width
        self.height = height
        self.x, self.y = pos
        self.duration = duration
        self.isi = isi
        self.sf = sf
        self.contrast = contrast
        self.color = color
        self._logged = False

    @property
    def position(self):
        return self.x, self.y

    def on_start(self):

        if stimtype == 'grating':
            self.wholefield_stimulus = visual.GratingStim(win=self.window,
                                                          tex='sin',
                                                          sf=self.sf,
                                                          units='norm',  # if 'norm', sf units in cycles per stimulus
                                                          # (scaling with stim size)
                                                          size=[self.width, self.height],
                                                          pos=self.position,
                                                          interpolate=True,
                                                          color=self.color)

        if stimtype == 'random_image':
            self.wholefield_stimulus = visual.NoiseStim(win=self.window,
                                                        noiseType='image',
                                                        noiseImage='C:\\Users\\lbauer\\Pictures\\rand.png',  # from Thiele paper
                                                        imageComponent='Amplitude',  # or 'Amplitude', or 'Neither'
                                                        units='degFlat',
                                                        size=[self.width, self.height],
                                                        pos=self.position,
                                                        interpolate=True,
                                                        color=self.color)

        if stimtype == 'random':
            # width and height to define the size at which a saccade will still keep it in view
            # how to spatial frequency
            matrix = np.random.randint(2, size=(int(self.width*.1), int(self.height*.1))).astype(bool)
            img = Image.fromarray(matrix)
            self.wholefield_stimulus = visual.ImageStim(win=self.window,
                                                        image=img,
                                                        units='pix',  # 'degFlat' adjusts for curvature
                                                        size=[self.width, self.height],
                                                        mask=matrix,
                                                        pos=self.position,
                                                        interpolate=True,
                                                        color=self.color)

        if stimtype == 'bw':
            # stimulus defined by sf and contrast.

            # Convert spatial frequency from degrees to pixels
            stim_size = [self.width, self.height]  # Size of the stimulus in degrees

            # Calculate stimulus size in pixels
            # TODO actually calculate the pixel size
            pixel_size = 0.1  # pixel size on the screen times how many pixels a degree is on your setup
            stim_size_pix = [int(x / pixel_size) for x in stim_size]

            # Generate noise texture
            noise_size_pix = [int(x / pixel_size / sf) for x in stim_size]
            noise = np.random.rand(*noise_size_pix) * 2 - 1
            noise = noise * self.contrast
            noise = np.repeat(np.repeat(noise, sf, axis=0), sf, axis=1)

            # Generate noise texture
            self.wholefield_stimulus = visual.GratingStim(win=self.window, tex=noise, mask=None, size=stim_size_pix, pos=self.position,
                                            contrast=self.contrast, units='pix')

        self.wholefield_stimulus.setAutoDraw(True)
        self.t_end = time.time() + self.duration

    def update(self):
        self.wholefield_stimulus.draw()
        t = time.time()
        if t >= self.t_end:
            self.finished = True
            return

    def on_stop(self):
        self.wholefield_stimulus.pos = [0, 0]

    def reset(self):
        super().reset()
        self._logged = False

    def log(self) -> dict:
        if not self._logged:
            self._logged = True
            return {"x": self.x, "y": self.y, "stimulus": "whole_field", "vector x": self.dx, "vector y": self.dy,
                    "width": self.width, "height": self.height}


class PseudoSaccade(WholeFieldStimulus):

    def __init__(self, width, height, pos: tuple, isi, duration: float, motion_vector, saccade_duration,
                 sf, contrast, stimtype, *args, **kwargs):
        super().__init__(width, height, pos, duration, isi, sf, contrast, stimtype, *args, **kwargs)
        """Object for Pseudosaccade stimulus, one round. Takes the WholefieldStimulus and moves it dependent on 
        where you are in the stimulus presentation duration. """
        self.width = width
        self.height = height
        self.motion_vector = motion_vector
        self.dx, self.dy = motion_vector
        self.x0, self.y0 = pos
        self.sf = sf
        self.contrast = contrast
        self.isi = isi
        self.saccade_duration = saccade_duration

    def on_start(self):
        super().on_start()
        t = time.time()
        self.t_pre_saccade = t + self.isi
        self.t_saccade = t + self.isi + self.saccade_duration

    def update(self):
        """at every update, check where in the stim paradigm you are, act accordingly"""
        # set the next xy position
        if self.t_pre_saccade <= time.time() <= self.t_saccade:  # if it's saccade time
            # saccade
            print('saccadesing')
            # the saccade speed in the motion vector is degrees per second
            # what we want is to define that in pixels per frame
            # 1280 pixels is 100 degrees
            framerate = 60  # TODO make this flexible. This is for Lisa's LightCrafter
            vector = [vector_degrees / framerate * 1280 / 100 for vector_degrees in self.motion_vector]
            self.dx, self.dy = vector
            pass
        else:  # if it's not saccade time
            # don't
            self.dx, self.dy = [0, 0]

        self.x = float(np.round(self.x + self.dx, 2))
        self.y = float(np.round(self.y + self.dy, 2))
        self.wholefield_stimulus.setPos(self.position)
        super().update()

    def reset(self):
        super().reset()
        self.x = self.x0
        self.y = self.y0
        self.wholefield_stimulus.setAutoDraw(False)
        self.window.flip()

    def log(self) -> dict:
        return {"x": self.x, "y": self.y, "stimulus": "pseudo_saccade", "vector x": self.dx, "vector y": self.dy, "width":
            self.width, "height": self.height}


class Pseudosaccades(RandomMultiStim):
    """Class that defines the stimulus list. In this case PseudoSaccade.
    Inhereits from RandomMultiStim that present the stimulus in create_stimulus_list randomly for n_presentations"""

    def __init__(self, width, height, locations, isi, duration, movement_vector, saccade_duration, sf, contrast,
                 stimytype, n_presentations, n_non_stimulus, *args, **kwargs):
        super().__init__(locations, isi, duration, n_presentations, n_non_stimulus, *args, **kwargs)
        self.saccade_duration = saccade_duration
        self.width = width
        self.height = height
        self.movement_vector = movement_vector
        self.sf = sf
        self.contrast = contrast
        self.stimtype = stimtype

    def create_stimulus_list(self):
        return [PseudoSaccade(self.width, self.height, location, self.isi, self.duration, self.movement_vector,
                              self.saccade_duration, self.sf, self.contrast, self.stimtype) for
                location in self.locations]


my_monitor = monitors.Monitor(u'Lisa_Monitor')
screen_size = my_monitor.getSizePix()
units = 'degFlat'

# Parameters that don't change
locations = [[0, 0]]
width = 360  # whatever covers the screen
height = 360  # whatever covers the screen

# Parameters that don't change after you're happy with the stimulus
movement_vector = (-90, 0)  # How fast is the saccade in degrees per second?
sf = 5  # What is the spatial frequency of the grating? In cycles per stimulus\
contrast = 1  # defining the luminance
saccade_duration = 0.3

# Parameters that do change for testing
isi = 30  # At least 30 for experiments
duration = isi * 2 + saccade_duration * 1  # stimulus duration. For now the plan is stationary grating, move, stationary
# grating, move, stationary grating, end.

# how many presentations?
n_presentations = 10  # I need enough that I get some without eye movements, 10?
n_non_stimulus = 0  # randomly?

stimtype = 'bw'

# this is imported and run by Pydra
# TODO add dark stim at the start, ~10 minutes.
# TODO add non moving Wholefieldstim at the start, ~10 minutes.movement_vector
stimulus_list = [Pseudosaccades(width, height, locations, isi, duration, movement_vector, saccade_duration, sf, contrast,
                 stimtype, n_presentations, n_non_stimulus)]

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
                         screen=-1)
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
