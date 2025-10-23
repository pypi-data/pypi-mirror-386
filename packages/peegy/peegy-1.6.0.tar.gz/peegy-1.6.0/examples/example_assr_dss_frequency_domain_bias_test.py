"""
.. _tut-assr-ht2-test-frequency-dss-bias-sim:

#####################################################################
ASSR using DSS and bootstrapping in the frequency-domain (Simulated)
#####################################################################

In this example we simulate a low-frequency ASSR, and we assess its significance using the Hotelling's T2 test and
F-test.
The background-noise is pink (controlled by noise attenuation = 3) and the presence of the signal is controlled by
return_noise_only=False (if True, only the noise is returned).
The signal is equal in all channels so that the detection rate obtained by keeping components can be assessed.
The spatial filter is biased using the covariance obtained in the frequency-domain.
Here, DSS is set-up to preserve only the first component, resulting in a very agressive filter prone to show biases in
absence of a target signal. To avoid this bias towards false positive a bootstrap approach is used.
To assess the false positive rate, the parameter return_noise_only should be set to True.

"""
# Enable below for interactive backend
# import matplotlib
# if 'Qt5Agg' in matplotlib.rcsetup.all_backends:
#     matplotlib.use('Qt5Agg')
from peegy.processing.pipe.pipeline import PipePool
from peegy.processing.pipe.definitions import Events, Domain
from peegy.processing.pipe.general import ReferenceData, FilterData, AutoRemoveBadChannels, RemoveBadChannels
from peegy.processing.pipe.epochs import AverageEpochsFrequencyDomain, AverageEpochs, EpochData
from peegy.processing.pipe.bootstrap.bootstrap import Bootstrap, BootstrapTarget
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


fs = 128.0 * u.Hz
epoch_length = 4.0 * u.s
epoch_length = np.ceil(epoch_length * fs) / fs  # fit to fs rate
assr_frequency = 6.75 * u.Hz
assr_frequency = np.ceil(epoch_length * assr_frequency) / epoch_length  # fit to epoch length

join_frequencies = np.arange(1, 4) * assr_frequency
# here we pick some random frequencies to test statistical detection
random_frequencies = np.unique(np.random.rand(2)*5) * u.Hz

test_frequencies = np.array([assr_frequency.value]) * u.Hz
weigh_frequencies = np.array([assr_frequency.value]) * u.Hz
template_waveform, _ = aep(fs=fs)
n_channels = 32
event_times = np.arange(0, 360.0, 1 / assr_frequency.to(u.Hz).value)
reader = GenerateInputData(template_waveform=template_waveform,
                           fs=fs,
                           n_channels=n_channels,
                           snr=0.001,
                           layout_file_name='biosemi32.lay',
                           event_times=event_times,
                           event_code=1.0,
                           include_eog_events=True,
                           figures_subset_folder='assr_dss_frequency_domain_test',
                           return_noise_only=False,
                           mixing_matrix=np.diag(np.ones(n_channels))/n_channels,
                           noise_attenuation=3,
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

pipeline['channel_cleaned_0'] = AutoRemoveBadChannels(reader)
pipeline['channel_cleaned'] = RemoveBadChannels(pipeline['channel_cleaned_0'],
                                                bad_channels='EOG1')
pipeline.run()

pipeline['time_filtered_data'] = FilterData(pipeline['channel_cleaned'],
                                            high_pass=2.0 * u.Hz,
                                            low_pass=48.0 * u.Hz)

pipeline['time_epochs'] = EpochData(pipeline['time_filtered_data'],
                                    event_code=1.0,
                                    post_stimulus_interval=epoch_length,
                                    base_line_correction=False)
pipeline.run()

# %%
# Plot components in the frequency-domain
# ---------------------------------------
# Spatial filter is a applied in the frequency-domain

pipeline['dss_time_epochs'] = CreateAndApplySpatialFilter(pipeline['time_epochs'],
                                                          sf_join_frequencies=join_frequencies,
                                                          test_frequencies=test_frequencies,
                                                          sf_components=np.arange(1),
                                                          projection_domain=Domain.frequency,
                                                          block_size=1,
                                                          weight_across_epochs=False,
                                                          return_figures=True,
                                                          delta_frequency=2 * u.Hz,
                                                          plot_y_lim=[0, 5])
pipeline.run()

# %%
# Average epochs
# ---------------------------------------
# We compute the average and simultaneously get statistical tests on the test_frequencies


pipeline['fft_ave'] = AverageEpochsFrequencyDomain(pipeline['dss_time_epochs'],
                                                   n_fft=int(epoch_length*fs),
                                                   weight_frequencies=weigh_frequencies,
                                                   test_frequencies=test_frequencies,
                                                   delta_frequency=2 * u.Hz)
pipeline['time_ave'] = AverageEpochs(pipeline['dss_time_epochs'])

pipeline['std_fft_ave'] = AverageEpochsFrequencyDomain(pipeline['time_epochs'],
                                                       n_fft=int(epoch_length * fs),
                                                       weight_frequencies=weigh_frequencies,
                                                       weight_across_epochs=False,
                                                       block_size=1,
                                                       test_frequencies=test_frequencies,
                                                       delta_frequency=2 * u.Hz)
pipeline.run()


# %%
# Bootstrapping
# ------------------------------------
# We generate a new pipeline indicating what would be bootstrapped
pipeline_bootstrap = PipePool()

pipeline_bootstrap['time_epochs'] = EpochData(pipeline['time_filtered_data'],
                                              event_code=1.0,
                                              post_stimulus_interval=epoch_length)
pipeline_bootstrap['time_epochs_dss'] = CreateAndApplySpatialFilter(pipeline_bootstrap['time_epochs'],
                                                                    sf_join_frequencies=join_frequencies,
                                                                    test_frequencies=test_frequencies,
                                                                    sf_components=np.arange(1),
                                                                    projection_domain=Domain.frequency,
                                                                    block_size=1,
                                                                    return_figures=False,
                                                                    components_to_plot=None,
                                                                    weight_across_epochs=False,
                                                                    weight_data=True,
                                                                    plot_power=False,
                                                                    delta_frequency=2 * u.Hz)

pipeline_bootstrap['ht2'] = AverageEpochsFrequencyDomain(pipeline_bootstrap['time_epochs_dss'],
                                                         n_fft=int(epoch_length * fs),
                                                         weight_frequencies=weigh_frequencies,
                                                         test_frequencies=test_frequencies,
                                                         delta_frequency=2 * u.Hz)
pipeline_bootstrap['f_test'] = FTest(pipeline_bootstrap['ht2'],
                                     n_fft=int(epoch_length * fs),
                                     test_frequencies=test_frequencies,
                                     delta_frequency=6 * u.Hz)


# bootstrap the pipe
pipeline['bootstrap'] = Bootstrap(
    n_jobs=6,
    at_each_bootstrap_do=pipeline_bootstrap,
    n_bootstraps=100,
    epoch_length=epoch_length,
    event_code=1.0,
    bootstrap_targets=[
        BootstrapTarget(
            test_name='HT2',
            group_by=['channel', 'frequency_tested'],
            target_values=['f', 'rn', 'snr']),
        BootstrapTarget(
            test_name='F-test',
            group_by=['channel', 'frequency_tested'],
            target_values=['f', 'rn', 'snr'])
    ])

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

pipeline['std_fft_ave_gfp_ftest'] = FTest(
    pipeline['std_fft_ave_gfp'],
    test_frequencies=test_frequencies,
    delta_frequency=5 * u.Hz)
pipeline.run()

pipeline['fft_ave'].output_node.statistical_tests['hotelling_t2_freq'][[
    "test_name", "df_1", "df_2", "f", "f_critic", "p_value"]].head()


ht2 = pipeline['fft_ave'].output_node.statistical_tests['hotelling_t2_freq']
print('\n HT2-Test \n'
      'n = {:} \n'
      'detections = {:} \n'
      'Detection rate {:} %'.format(ht2.shape[0],
                                    np.sum(ht2["p_value"] < 0.05),
                                    np.round(100 * np.sum(ht2["p_value"] < 0.05) / ht2.shape[0],
                                             decimals=2)))

f_test = pipeline['fft_ave_gfp_ftest'].output_node.statistical_tests['f_test_freq']
print('\n F-Test \n'
      'n = {:} \n'
      'detections = {:} \n'
      'Detection rate {:} %'.format(f_test.shape[0],
                                    np.sum(f_test["p_value"] < 0.05),
                                    np.round(100 * np.sum(f_test["p_value"] < 0.05) / f_test.shape[0],
                                             decimals=2)))

boot_h = pipeline['bootstrap'].output_node.statistical_tests['bootstrap'].query(
    'statistic == "f" and test_name == "HT2"')
print('\n Bootstrap HT2-Test \n'
      'n = {:} \n'
      'detections = {:} \n'
      'Detection rate {:} %'.format(boot_h.shape[0],
                                    np.sum(boot_h["p_value"] < 0.05),
                                    np.round(100 * np.sum(boot_h["p_value"] < 0.05) / boot_h.shape[0],
                                             decimals=2)))

boot_f = pipeline['bootstrap'].output_node.statistical_tests['bootstrap'].query(
    'statistic == "f" and test_name == "F-test"')
print('\n Bootstrap F-Test \n'
      'n = {:} \n'
      'detections = {:} \n'
      'Detection rate {:} %'.format(boot_f.shape[0],
                                    np.sum(boot_f["p_value"] < 0.05),
                                    np.round(100 * np.sum(boot_f["p_value"] < 0.05) / boot_f.shape[0],
                                             decimals=2)))
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
database_path = reader.input_node.paths.file_directory + os.sep + 'assr_dss_frequency_domain_test.sqlite'
pipeline['database'] = SaveToDatabase(database_path=database_path,
                                      measurement_information=measurement_info,
                                      subject_information=subject_info,
                                      recording_information={'recording_device': 'dummy_device'},
                                      stimuli_information=_parameters,
                                      processes_list=[pipeline['fft_ave_gfp'],
                                                      pipeline['std_fft_ave_gfp'],
                                                      pipeline['time_ave'],
                                                      pipeline['bootstrap']],
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
