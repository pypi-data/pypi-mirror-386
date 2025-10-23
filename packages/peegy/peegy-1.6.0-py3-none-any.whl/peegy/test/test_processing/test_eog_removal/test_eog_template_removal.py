from peegy.processing.tools.epochs_processing_tools import et_subtract_oeg_template
from peegy.processing.tools.multiprocessing.multiprocessesing_filter import filt_data
from peegy.processing.tools.template_generator.auditory_waveforms import eog
import numpy as np
from numpy import matlib
import matplotlib.pyplot as plt
import astropy.units as u
import matplotlib
if 'Qt5Agg' in matplotlib.rcsetup.all_backends:
    matplotlib.use('Qt5Agg')


def unitary_step(x: type(np.array) | None = None):
    return (x > 0).astype(float)


np.random.seed(7123)
n_ch = 10
fs = 16384.0 * u.Hz
recording_time = 180
eog_rate = 1 / 4 * u.Hz
time = np.arange(0, recording_time, 1/fs.to(u.Hz).value)
time_artefact = np.arange(0, 1/3, 1/fs.to(u.Hz).value)
n_events = int(recording_time // (1 / eog_rate.to(u.Hz).value))
# we generate a fake low frequency artefact signal and generate a mixing matrix
eog1_template, _ = eog(fs)
# eog1_template *= unitary_step(eog1_template)

events = np.zeros(time.size, )
_intervals = 1/eog_rate.to(u.Hz).value + 0.5 * np.random.randn(n_events, )
event_times = np.cumsum(_intervals)
event_times = event_times[event_times < recording_time]
_idx = np.minimum(event_times * fs.to(u.Hz).value, time.size - 1).astype(int)
events[_idx] = 1 + 0.5 * np.random.rand(_idx.size)
eog1 = filt_data(eog1_template.reshape(-1, 1), events.flatten(), mode='full').flatten()
eog1 = eog1[0: time.size]
w1 = np.random.rand(1, n_ch)
eog1mix = matlib.repmat(eog1, n_ch, 1).T * w1
eog1mix[:, -1] = eog1

# generate EEG data at a higher frequency
ep = 0.1 * np.sin(2 * np.pi * 137.0 * time)
w3 = np.random.rand(1, n_ch)
epochs = matlib.repmat(ep, n_ch, 1).T * w3 * u.uV
epochs[:, -1:] = 0

# generate noise and mixing matrix
ns = np.random.randn(*time.shape)
w4 = np.random.rand(1, n_ch)
noise = 40 * matlib.repmat(ns, n_ch, 1).T * w4 * u.uV

# mix all data
data = eog1mix + epochs + noise
ref_idx = np.array([9])

# apply rise-fade window
fade_in_out = np.ones(data.shape)
fade_len = round(time.size // 40)
fade_in_out[0: fade_len, :] = (np.sin(2 * np.pi * (1 / (4 * fade_len / fs.to(u.Hz).value)) *
                                      time[0: fade_len]) ** 2)[:, None]
fade_in_out[-fade_len:, :] = (np.sin(2 * np.pi * (1 / (4 * fade_len / fs.to(u.Hz).value)) *
                                     time[0: fade_len] + np.pi / 2) ** 2)[:, None]
data *= fade_in_out
# remove artefacts
clean_data, fig_results = et_subtract_oeg_template(data=data,
                                                   idx_ref=ref_idx,
                                                   fs=fs,
                                                   plot_results=True,
                                                   high_pass=0.01 * u.Hz,
                                                   low_pass=20 * u.Hz,
                                                   minimum_interval_width=0.2 * u.s,
                                                   kernel_bandwidth=0.15)

# get frequency responses
freq = np.arange(0, time.size) * fs / time.size
yfft_data = np.abs(np.fft.fft(data, axis=0))
yfft_clean = np.abs(np.fft.fft(clean_data, axis=0))

fig = plt.figure()
ax = fig.add_subplot(221)
ax.plot(time, np.squeeze(data[:, 0]), label='contaminated')
ax.plot(time, np.squeeze(clean_data[:,  0]), label='clean')
ax = fig.add_subplot(222)
ax.plot(freq, np.squeeze(yfft_data[:, 0]), label='contaminated fft')
ax.plot(freq, np.squeeze(yfft_clean[:, 0]), label='clean fft')
ax.set_xlim(0, 200)
plt.legend()
plt.show()
