# Import necessary modules
from psychopy import visual, core, event, monitors
import numpy as np
import time


def create_bw_noise(sf, contrast):
    # Create Gaussian noise texture

    # Convert spatial frequency from degrees to pixels
    stim_size = [720, 720]  # Size of the stimulus in degrees

    # Calculate stimulus size in pixels
    pixel_size = 0.01 * 20
    stim_size_pix = [int(x / pixel_size) for x in stim_size]

    # Generate noise texture
    noise_size_pix = [int(x / pixel_size / sf) for x in stim_size]
    noise = np.random.rand(*noise_size_pix) * 2 - 1
    noise = noise * contrast
    noise = np.repeat(np.repeat(noise, sf, axis=0), sf, axis=1)

    # Generate noise texture
    noise_stim = visual.GratingStim(win=win, tex=noise, mask=None, size=stim_size_pix,
                                   contrast=contrast, units='pix')

    return noise_stim


# Create window to present stimuli on
win = visual.Window(size=(800, 600), fullscr=False)

# Set initial position of stimulus to center of screen
stim_pos = (0, 0)

# Set spatial frequency and contrast parameters
spatial_freq = 15
contrast = 30  # defines the luminance

# Create white noise stimulus with specified spatial frequency and amplitude
noise_stim = create_bw_noise(spatial_freq, contrast)

noise_stim.draw()
# Flip window to update screen
win.flip()
time.sleep(30)



