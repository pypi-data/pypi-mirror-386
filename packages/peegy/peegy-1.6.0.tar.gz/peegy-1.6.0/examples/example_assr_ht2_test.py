"""
.. _tut-assr-ht2-test-sim:

##############################################
ASSR Hotelling-T2 test (Simulated)
##############################################

In this example we simulate an ASSR, and we assess its significance using the Hotelling's T2 test.
This method uses the real and imaginary part of the frequency bin of interest to assess whether the points from
each epoch are significantly different from zero (the center of the polar complex-plane)

"""
# Enable below for interactive backend
# import matplotlib
# if 'Qt5Agg' in matplotlib.rcsetup.all_backends:
#     matplotlib.use('Qt5Agg')
from peegy.processing.pipe.pipeline import PipePool
from peegy.processing.pipe.definitions import Events, Domain
from peegy.processing.pipe.general import ReferenceData, FilterData, AutoRemoveBadChannels
from peegy.processing.pipe.epochs import AverageEpochsFrequencyDomain, AverageEpochs, EpochData
from peegy.processing.pipe.attach import AppendGFPChannel
from peegy.processing.pipe.statistics import FTest
from peegy.processing.pipe.plot import PlotWaveforms, PlotTopographicMap
from peegy.processing.pipe.spatial_filtering import CreateAndApplySpatialFilter
from peegy.processing.pipe.simulate import GenerateInputData
from peegy.processing.tools.template_generator.auditory_waveforms import aep
from peegy.processing.pipe.storage import MeasurementInformation, SubjectInformation, SaveToDatabase
from peegy.io.storage.data_storage_reading_tools import sqlite_tables_to_pandas, sqlite_waveforms_to_pandas
from peegy.io.storage.plot_tools import plot_time_frequency_responses, plot_topographic_maps
import os
import astropy.units as u
import numpy as np


# %%
# Generate some data
# ===================
# We generate some auditory steady-state response (ASSR)


fs = 256.0 * u.Hz
epoch_length = 4.0 * u.s
epoch_length = np.ceil(epoch_length * fs) / fs  # fit to fs rate
assr_frequency = 41.0 * u.Hz
assr_frequency = np.ceil(epoch_length * assr_frequency) / epoch_length  # fit to epoch length

# here we pick some random frequencies to test statistical detection
random_frequencies = np.unique(np.random.rand(2)*5) * u.Hz

test_frequencies = np.concatenate((
    [assr_frequency,
     2 * assr_frequency],
    random_frequencies))

template_waveform, _ = aep(fs=fs)
n_channels = 32
event_times = np.arange(0, 360.0, 1 / assr_frequency.to(u.Hz).value)
reader = GenerateInputData(template_waveform=template_waveform,
                           fs=fs,
                           n_channels=n_channels,
                           mixing_matrix=np.diag(np.arange(n_channels)) / n_channels,
                           snr=0.05,
                           layout_file_name='biosemi32.lay',
                           event_times=event_times,
                           event_code=1.0,
                           figures_subset_folder='assr_ht2_test',
                           noise_seed=0)
reader.run()

# %%
# Resize events
# ===================
# Now we keep events at intervals that correspond to our desired epoch length


events = reader.output_node.events.get_events(code=1)
# skip events to preserve only those at each epoch point
_new_events = Events(events=events[0:-1:int(epoch_length * assr_frequency)])
reader.output_node.events = _new_events

# %%
# Start the pipeline
# ===================
# Some processing to obtain clean epochs

pipeline = PipePool()
pipeline['referenced'] = ReferenceData(reader,
                                       reference_channels=['Cz'],
                                       invert_polarity=True)
pipeline['channel_cleaned'] = AutoRemoveBadChannels(pipeline['referenced'])

pipeline['time_filtered_data'] = FilterData(pipeline['channel_cleaned'],
                                            high_pass=2.0 * u.Hz,
                                            low_pass=100.0 * u.Hz)
pipeline['time_epochs'] = EpochData(pipeline['time_filtered_data'],
                                    event_code=1.0,
                                    base_line_correction=False)
pipeline.run()

# %%
# Plot components in the frequency-domain
# ---------------------------------------
# Spatial filter is a applied in the frequency-domain

pipeline['dss_time_epochs'] = CreateAndApplySpatialFilter(pipeline['time_epochs'],
                                                          block_size=10,
                                                          return_figures=True,
                                                          projection_domain=Domain.frequency,
                                                          plot_y_lim=[0, 0.2])
pipeline.run()

# %%
# Average epochs
# ---------------------------------------
# We compute the average and simultaneously get statistical tests on the test_frequencies


pipeline['fft_ave'] = AverageEpochsFrequencyDomain(pipeline['dss_time_epochs'],
                                                   n_fft=int(epoch_length*fs),
                                                   weight_frequencies=assr_frequency,
                                                   test_frequencies=test_frequencies,
                                                   delta_frequency=2 * u.Hz)
pipeline['time_ave'] = AverageEpochs(pipeline['dss_time_epochs'])

pipeline['std_fft_ave'] = AverageEpochsFrequencyDomain(pipeline['time_epochs'],
                                                       n_fft=int(epoch_length * fs),
                                                       weight_frequencies=assr_frequency,
                                                       test_frequencies=test_frequencies,
                                                       delta_frequency=2 * u.Hz)
pipeline.run()

# %%
# Compute global field power (GFP)
# ---------------------------------------
# We compute the GFP across channels and epochs. A new channel with the GFP is appended to the data

pipeline['fft_ave_gfp'] = AppendGFPChannel(pipeline['fft_ave'])
pipeline.run()

pipeline['std_fft_ave_gfp'] = AppendGFPChannel(pipeline['std_fft_ave'])
pipeline.run()

pipeline['fft_ave_gfp_ftest'] = FTest(
    pipeline['fft_ave_gfp'],
    test_frequencies=test_frequencies,
    delta_frequency=5 * u.Hz)
pipeline.run()
pipeline['std_fft_ave_gfp_ftest'] = FTest(
    pipeline['std_fft_ave_gfp'],
    test_frequencies=test_frequencies,
    delta_frequency=5 * u.Hz)
pipeline.run()

pipeline['fft_ave'].output_node.statistical_tests['hotelling_t2_freq'][
    ["test_name", "df_1", "df_2", "f", "f_critic", "p_value"]].head()
pipeline.run()

# %%
# Generate figures
# ---------------------------------------
# Now we run plot the average waveforms and show the stats


pipeline['waveform_plotter'] = PlotWaveforms(pipeline['fft_ave_gfp_ftest'],
                                             overlay=[pipeline['std_fft_ave_gfp_ftest']],
                                             plot_x_lim=[0, 90],
                                             ch_to_plot=np.array(['O2', 'T8', 'T7', 'GFP']),
                                             statistical_test='f_test_freq',
                                             show_following_stats=['f'],
                                             return_figures=True,
                                             user_naming_rule='standard_and_dss')
pipeline.run()
pipeline['topographic_map'] = PlotTopographicMap(pipeline['fft_ave'],
                                                 topographic_channels=np.array(['O2', 'T8', 'T7', 'GFP']),
                                                 plot_x_lim=[0, 90],
                                                 plot_y_lim=[0, 6],
                                                 return_figures=True)
pipeline.run()

# %%
# Save results to a database
# ---------------------------------------
# We get the measurements we are interested in and save them into a database

subject_info = SubjectInformation(subject_id='Test_Subject')
measurement_info = MeasurementInformation(
    date='Today',
    experiment='sim')

_parameters = {'Type': 'ASSR'}
database_path = reader.input_node.paths.file_directory + os.sep + 'assr_ht2_test.sqlite'
pipeline['database'] = SaveToDatabase(database_path=database_path,
                                      measurement_information=measurement_info,
                                      subject_information=subject_info,
                                      recording_information={'recording_device': 'dummy_device'},
                                      stimuli_information=_parameters,
                                      processes_list=[pipeline['fft_ave_gfp'],
                                                      pipeline['std_fft_ave_gfp'],
                                                      pipeline['time_ave']],
                                      include_waveforms=True
                                      )
pipeline.run()

# %%
# Generate pipeline diagram
# ------------------------------------
pipeline.diagram(file_name=reader.output_node.paths.figures_current_dir + 'pipeline.png',
                 return_figure=True,
                 dpi=600)


# Read waveforms from generated database and plot them
# ------------------------------------
df_waves = sqlite_waveforms_to_pandas(database_path=database_path,
                                      group_factors=['data_source', 'channel'],
                                      channels=['T8', 'T7'])

fig_out_1 = plot_time_frequency_responses(dataframe=df_waves,
                                          rows_by='channel',
                                          cols_by='data_source',
                                          title_by='col',
                                          show_legend=True)

fig_out_2 = plot_time_frequency_responses(dataframe=df_waves,
                                          rows_by='channel',
                                          cols_by='domain',
                                          title_by='both',
                                          show_legend=True)

fig_out_3 = plot_time_frequency_responses(dataframe=df_waves,
                                          rows_by='channel',
                                          cols_by='domain',
                                          title_by='both',
                                          show_legend=True)

df_ht2 = sqlite_tables_to_pandas(database_path=database_path,
                                 tables=['hotelling_t2_freq'])['hotelling_t2_freq']

# We show the topographic maps for the two Hotelling T2 (standard processing and denoise using dss)

fig_out_4 = plot_topographic_maps(dataframe=df_ht2,
                                  channels_column='channel',
                                  rows_by='data_source',
                                  layout='biosemi32.lay',
                                  color_map_label='Amplitude [uV]',
                                  topographic_value='mean_amplitude')
