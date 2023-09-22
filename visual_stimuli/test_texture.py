import numpy as np

from psychopy import filters, visual
import matplotlib.pyplot as plt

# possible stim production way: https://www.sciencedirect.com/science/article/pii/S0960982220305571#bib20 Glider Stim

# win = visual.Window([800, 600], monitor="testMonitor", units="deg")
#

def makeFilteredNoise(res, radius, shape='gauss'):
    """https://discourse.psychopy.org/t/creating-bandpass-gaussian-white-noise/2125
    The units are "fractions of the stimulus", the radius is specified to 3xSigma. So,
    if you have a stimulus width of 3 degrees (1.5 radius), then setting the filter radius to
    0.1 means that the radius was actually 0.1*(3/2) = 0.15 degrees = 3xSigma. So the gaussian filter,
    in terms of its sigma, would be 0.05 degrees."""
    noise = np.random.random([res, res])
    kernel = filters.makeMask(res, shape=shape, radius=radius)
    filteredNoise = filters.conv2d(kernel, noise)
    filteredNoise = (filteredNoise - filteredNoise.min()) / (filteredNoise.max() - filteredNoise.min()) * 2 - 1
    return filteredNoise


def makeFourierTransform(image, plot=True):
    """Joe's way of Fourier transforming an image to a notquiterealimage"""

    if image =='random':
        image = np.random.random([512, 512])

    # transform image
    transform = np.fft.fftshift(np.fft.fft2(image))

    freq = np.abs(transform)  # get the frequency
    phase = np.angle(transform)  # get the phase

    notquiterealimage = np.fft.ifft2(np.fft.fftshift(freq * np.exp(1j * phase))).astype('float')

    if plot:
        plt.figure()
        plt.imshow(notquiterealimage)
        plt.figure()
        plt.imshow(image)

    return notquiterealimage

import imageio
im = imageio.imread('C:\\Users\\lbauer\\Pictures\\rand.png')
print(im.shape)
image = im[:512, :512, 0]

image = makeFilteredNoise()

t = np.fft.fftshift(np.fft.fft2(image))

freq = np.abs(t)
phase = np.angle(t)

notquiterealimage = np.fft.ifft2(np.fft.fftshift(freq * np.exp(1j * phase))).astype('float')

plt.imshow(notquiterealimage)
plt.figure()
plt.imshow(image)

# if stimtype == 'randomnoise':
#     self.wholefield_stimulus = visual.ImageStim(win=self.window,
#                                                 image=filteredNoise,
#                                                 mask=None,
#                                                 tex='sin',
#                                                 sf=self.sf,
#                                                 units='norm',  # if 'norm', sf units in cycles per stimulus
#                                                 # (scaling with stim size)
#                                                 size=[self.width, self.height],
#                                                 pos=self.position,
#                                                 interpolate=True,
#                                                 color=self.color)

size = 5  # size of the 3 gabors in degrees
spafreq = 4  # number of grating cycles
filteredNoise = makeFilteredNoise(512, (size / spafreq) / 2)
stim = makeFourierTransform(filteredNoise, True)

noise3 = visual.GratingStim(win, tex=filteredNoise,
                            size=[size, size],
                            units='deg', mask='gauss', pos=[0, 0],
                            interpolate=False, ori=0, autoLog=False)

stim.draw()

win.flip()


def makeNoise(win, image):
    noise = visual.NoiseStim(
        win=win, name='noise', units='pix',
        noiseImage=image, mask=None,
        ori=1.0, pos=(0, 0), size=(512, 512), sf=None, phase=0,
        color=[1, 1, 1], colorSpace='rgb', opacity=1, blendmode='add', contrast=1.0,
        texRes=512, filter='None', imageComponent='Phase',
        noiseType='Gabor', noiseElementSize=4, noiseBaseSf=32.0 / 512,
        noiseBW=1.0, noiseBWO=30, noiseFractalPower=-1, noiseFilterLower=3 / 512, noiseFilterUpper=8.0 / 512.0,
        noiseFilterOrder=3.0, noiseClip=3.0, interpolate=False, depth=-1.0)
    return noise

