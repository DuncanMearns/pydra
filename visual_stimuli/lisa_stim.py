from pydra.modules.visual_stimulation import Stimulus, Wait
from psychopy import monitors, visual
import numpy as np
import time

my_monitor = monitors.Monitor(u'Lisa_Monitor')
screen_size = my_monitor.getSizePix()
units = 'degFlat'


class DotStimulus(Stimulus):
    """
    __init__ should take arguments that specify things about a given stimulus

    `on_start` is called when stimulus starts
    then `update` is called until `self.finished` flag is set to True
    then `on_stop` is called
    """

    def __init__(self, size: float, pos: tuple, duration: float, color: tuple = (1, 1, 1), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.size = size
        self.x, self.y = pos
        self.duration = duration
        self.color = color
        self._logged = False

    @property
    def position(self):
        return self.x, self.y

    def on_start(self):
        self.dot = visual.Circle(win=self.window,
                                 radius=self.size,
                                 pos=self.position,
                                 fillColor=self.color,
                                 fillColorSpace=u'rgb',
                                 lineColor=self.color,
                                 lineColorSpace=u'rgb')
        self.dot.setAutoDraw(False)
        self.t_end = time.time() + self.duration

    def update(self):
        self.dot.draw()
        t = time.time()
        if t >= self.t_end:
            self.finished = True
            return

    def on_stop(self):
        self.dot.radius = 0

    def reset(self):
        super().reset()
        self._logged = False

    def log(self) -> dict:
        if not self._logged:
            self._logged = True
            return {"stimulus": self.position}


class RandomMultiDot(Stimulus):

    def __init__(self, size, locations, isi, duration, n_presentations=None, total_duration=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.locations = locations
        self.isi = isi
        self.size = size
        self.duration = duration
        self._n_presentations = n_presentations  # number of times each stimulus is displayed
        self._total_duration = total_duration

    @property
    def n_presentations(self):
        if self._n_presentations:
            return self._n_presentations
        elif self._total_duration:
            stim_time = self.duration + self.isi
            n_presentations = self._total_duration // stim_time
            return n_presentations
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

    def create_stimulus_list(self):
        return [DotStimulus(self.size, location, self.duration, color=(1, 1, 1)) for location in self.locations]

    def on_start(self):

        # create our Dot stimuli with each respective location
        self.list_of_stimuli = self.create_stimulus_list()
        for stimulus in self.list_of_stimuli:
            stimulus.window = self.window

        # Create wait stimulus
        self.wait_stimulus = Wait(self.isi)

        # Randomize stimulus presentation order
        stimulus_indices = list(range(len(self.locations))) * self.n_presentations
        self.stimulus_indices = np.random.permutation(stimulus_indices)
        self.current_idx = 0

        self.current_stimulus = self.list_of_stimuli[self.show_idx]  # make the current stimulus the dot stimulus
        print("Expected duration:", self.total_duration, "seconds")
        print(self.start_message(), end=" ")

    def update(self):
        ret = self.current_stimulus()  # calling the stimulus updates it, ret is whether stimulus has finished
        if ret:
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
        return self.current_stimulus.log()


# RandomMultiDot information
y = -10
locations = [[0, y], [10, y], [25, y], [-10, y], [-25, y]]
size = 1
isi = 1
duration = 3

stimulus_list = [RandomMultiDot(size, locations, isi, duration, n_presentations=1)]  # this is imported and run by Pydra


if __name__ == "__main__":
    # monitor setup
    bg_color = (-1, -1, -1)

    # window
    window_params = dict(size=screen_size,
                        fullscr=True,
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
            if ret:
                idx += 1
        except IndexError:
            break
