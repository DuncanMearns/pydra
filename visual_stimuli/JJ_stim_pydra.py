from itertools import chain, cycle

from pydra.modules.visual_stimulation import Stimulus, Wait
import numpy as np
import time
from psychopy import visual, monitors, core


def create_multiple_freqs(

        speed=.5 * 4.,
        rad=1.8 * 4.,
        delay=20.,
        start_angle=225,
        size=0.4 * 4.,
        freqs=(0.75, 1.5, 3.0, 6.0, 60.),
        freq_size={},
        offset=0.,
        fraction=1
):
    """ a function created by Johannes Kappel (JJ) in the Baier lab that seems to be accepting a number of parameters for
    a visual stimulus of a dot, which then all get appended to a dot_params list. Originally, this was then used as
    an argument for JJ's own run function. Or, directly, into the flicker dot params function."""

    base_dict = {
        'speed': speed,
        'rad': rad,
        'delay': delay,
        'start_angle': start_angle,
        'ccw': True,
        'boutrate': np.nan,
        'size': np.nan,
        'offset': offset,
        'fraction': fraction
    }
    dot_params = list()

    for freq in freqs:

        dict_instance = base_dict.copy()
        dict_instance['boutrate'] = freq
        dict_instance['size'] = size
        dict_instance['ccw'] = True
        dict_instance['offset'] *= -1

        dot_params.append(dict_instance)

        dict_instance = base_dict.copy()
        dict_instance['boutrate'] = freq
        dict_instance['size'] = size
        dict_instance['ccw'] = False

        dot_params.append(dict_instance)

        if freq in freq_size.keys():

            for fsize in freq_size[freq]:
                dict_instance = base_dict.copy()
                dict_instance['boutrate'] = freq
                dict_instance['size'] = fsize
                dict_instance['ccw'] = True

                dot_params.append(dict_instance)

                dict_instance = base_dict.copy()
                dict_instance['boutrate'] = freq
                dict_instance['size'] = fsize
                dict_instance['ccw'] = False

                dot_params.append(dict_instance)

    return dot_params


def circular_step(

        delay,
        speed=10.,
        ccw=False,
        rad=10.,
        size=.5,
        frate=60.,
        boutrate=2.,
        start_angle=None,
        offset=0,
        fraction=1.,
):
    """

    :param delay: int, delay in sec before stimulus start
    :param speed: float, stimulus speed in cm/sec
    :param ccw: bool, stimulus direction True=counter-clockwise
    :param rad: float, radius of circle
    :param size: float, diameter of stimulus
    :param frate: float, frame rate in fps
    :param boutrate: float, # of jumps per second
    :param start_angle: int, dot starting point in degrees, interpreted as in frontal view of the animal
    :param offset: int, offset from frontal view in degrees
    :param fraction: float, factor to reduce the trajectory of the dot stimulus to a specific fraction
    :return: xy locations of dot stimulus per frame, stimulus params
    """

    rad = float(rad)  # cm
    speed = float(speed)  # cm/s
    boutrate = float(boutrate)  # 1/s

    circ = float(2. * np.pi * rad) * fraction  # circumference
    period_rot = circ / float(speed)  # s (sec per rotation)

    ang_velocity = float(2. * np.pi) * fraction / float(period_rot)  # radians/s
    ang_velocity_f = ang_velocity * (1. / float(frate))  # radians/frame

    if start_angle is None:

        start_angle = np.deg2rad(0) + np.deg2rad(offset)

    else:

        start_angle = np.deg2rad(start_angle) + np.deg2rad(offset)

    x = rad * np.cos(start_angle)  # Starting x coordinate
    y = rad * np.sin(start_angle)  # Starting y coordinate

    xys = []
    bout = []

    nframes = 2 * np.pi * fraction / ang_velocity_f  # 2 * pi for whole rotation
    interval = round(frate / boutrate)

    new_angle = start_angle
    for frame in range(int(round(nframes) + 1)):

        if ccw:
            new_angle = new_angle - ang_velocity_f
        else:
            new_angle = new_angle + ang_velocity_f

        if frame % interval == 0:

            bout.append((x, y, new_angle))
            xys.append(bout)
            bout = []

            x = rad * np.cos(new_angle)
            y = rad * np.sin(new_angle)

        else:
            bout.append((x, y, new_angle))

    params = {
        'radius': rad,
        'speed': speed,
        'ccw': ccw,
        'frate': frate,
        'boutrate': boutrate,
        'delay': delay,
        'size': size,
        'start angle': start_angle,
        'offset': offset,
        'fraction': fraction
    }

    return list(chain(*xys)), params


class RandomMultiStim(Stimulus):
    """Your stimulus class that randomly shows a number of stimuli.
    Inherit this class into another that has the create_stimulus_list function."""

    def __init__(self, delay, duration, n_presentations,
                 total_duration=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_idx = None
        self.stimulus_indices = None
        self.wait_stimulus = None
        self.current_stimulus = None
        self.list_of_stimuli = None
        self.isi = delay
        self.duration = duration
        self._n_presentations = n_presentations  # number of times each stimulus is displayed
        self._total_duration = total_duration

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
        return f"Starting stimulus presentation"

    def on_start(self):
        # create our rect stimuli with each respective location
        self.list_of_stimuli = self.create_stimulus_list()
        for stimulus in self.list_of_stimuli:
            stimulus.window = self.window

        # Create wait stimulus
        self.wait_stimulus = Wait(self.isi)

        # Randomize stimulus presentation order
        stimulus_indices = list(range(1)) * self.n_presentations
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


class MovingDotBottom(Stimulus):

    def __init__(self, xys, params, delay, stimulus_duration, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """ Code originally written by Johannes Kappel and modified by Lisa Bauer. This is a function to display a dot
        stimulus. It takes a number of x y coordinates, then creates a dot using psychopy's visual.Circle function to
        display a dot in those coordinates. Flips the window, waits for 1, draws the dot, waits for 3, then draws the dot
        in each xy coordinate. Returns both the start and end timepoints. To create correct xy coordinates, you have to use
        another function. In my case, circular step. """

        self.xy_coordinates = xys
        self.start_params = params[0]
        self.stimulus_duration = stimulus_duration
        self.delay = delay

        self.xy_cycle = cycle(self.xy_coordinates)
        self.x, self.y = next(self.xy_cycle)[:2]

    @property
    def position(self):
        return self.x, self.y

    def on_start(self):
        self.dot_stimulus = visual.Circle(win=self.window,
                                          fillColor='black',
                                          fillColorSpace=u'rgb',
                                          lineColor='black',
                                          lineColorSpace=u'rgb',
                                          units='cm',
                                          size=self.start_params['size'],
                                          pos=[self.x, self.y])

        self.dot_stimulus.setAutoDraw(True)
        # window parameters JJ had
        self.window.color = (0, 0, 0)
        self.window.monitor = monitors.Monitor('default', width=8, distance=8)
        self.window.monitor.setSizePix((320, 200))

        for a in range(int(self.delay)):
            self.window.flip()
            core.wait(1)
        print('delay has ended')

        # get the starting and ending time of presenting the stimulus.
        self.t_start = time.time()
        self.t_end = time.time() + self.stimulus_duration
        super().on_start()

    def update(self):
        t = time.time()
        if t >= self.t_end:
            self.finished = True
            return

        self.x, self.y = next(self.xy_cycle)[:2]

        self.dot_stimulus.pos = [self.x, self.y]
        self.dot_stimulus.draw()
        self.window.flip()

        if self.x == self.xy_coordinates[-1][0] and self.y == self.xy_coordinates[-1][1]:
            print('one cycle completed, continuing with delay')
            self.cycle_completed()

        super().update()

    def on_stop(self):
        self.x = self.xy_coordinates[0][0]
        self.y = self.xy_coordinates[0][1]
        self.dot_stimulus.pos = (self.x, self.y)
        self.dot_stimulus.draw()
        self.window.flip()

    def cycle_completed(self):
        self.dot_stimulus.setAutoDraw(False)
        self.window.flip()
        for a in range(int(self.delay)):
            core.wait(1)
        self.dot_stimulus.setAutoDraw(True)

    def log(self) -> dict:
        return {"x": self.x, "y": self.y, "stimulus": "moving_dot_bottom"}


class MovingDotsBottom(RandomMultiStim):
    """Class that defines the stimulus list. In this case PseudoSaccade.
    Inhereits from RandomMultiStim that present the stimulus in create_stimulus_list randomly for n_presentations"""

    def __init__(self, all_xys, all_params, delay, stimulus_duration, n_presentations, *args, **kwargs):
        super().__init__(delay, stimulus_duration, n_presentations, *args, **kwargs)
        self.all_xys = all_xys
        self.all_params = all_params
        self.delay = delay
        self.stimulus_duration = stimulus_duration

    def create_stimulus_list(self):
        return [MovingDotBottom(self.all_xys, self.all_params, self.delay, self.stimulus_duration)]


# Stimulus for bottom circling moving dot.
# JJ original protocol
# These are the parameters JJ used to create a circular dot stimulus, should induce reliable wave response in Tectum
dot_params = create_multiple_freqs(
    speed=.5 * 4., # .5 * 4.
    rad=1.8 * 4.,
    delay=30.,
    start_angle=169,
    size=0.4 * 4.,
    freqs=[60.],
)

# the fps of the LightCrafter Projector is 60 frames per second
fps_screen = 60

all_xys = list()
all_params = list()
for p_idx, pr in enumerate(dot_params):
    xys, params = circular_step(
        frate=fps_screen,
        speed=pr['speed'],
        rad=pr['rad'],
        delay=pr['delay'],
        start_angle=pr['start_angle'],
        ccw=pr['ccw'],
        boutrate=pr['boutrate'],
        size=pr['size'],
        offset=pr['offset'],
        fraction=pr['fraction']
    )
    [all_xys.append(xys[n]) for n in range(0, len(xys))]
    [all_params.append(params) for n in range(0, len(xys))]

delay = 30
stimulus_duration = 1200
stimulus_list = [MovingDotsBottom(all_xys, all_params, delay, stimulus_duration, n_presentations=1)]

if __name__ == "__main__":

    # monitor setup
    def init_monitor(mon_name, fullscr=True):
        my_monitor = monitors.Monitor('default', width=8, distance=8)
        my_monitor.setSizePix((320, 200))
        screen_size = my_monitor.getSizePix()

        my_window = visual.Window(
            size=screen_size,
            fullscr=fullscr,
            screen=-1,
            allowGUI=True,
            allowStencil=False,
            monitor=my_monitor,
            color=[0, 0, 0],
            colorSpace=u'rgb',
            blendMode=u'avg',
            useFBO=True,
            units='cm',
            rgb=list(np.asarray([0, 0, 0])))

        return my_window


    my_window = init_monitor(mon_name=u'Lisa_Monitor', fullscr=True)

    for stim in stimulus_list:
        stim.window = my_window

    idx = 0
    while True:
        try:
            ret = stimulus_list[idx]()
            my_window.flip()
            Wait(delay)
            if ret:
                idx += 1
        except IndexError:
            break
    print("DONE!")
