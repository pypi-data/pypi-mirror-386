from peegy.processing.pipe.definitions import InputOutputProcess
from peegy.processing.tools.eeg_epoch_operators import w_mean
import numpy as np
import os
import astropy.units as u
from typing import List
from PyQt5.QtCore import QLibraryInfo
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = QLibraryInfo.location(QLibraryInfo.PluginsPath)


class AppendGFPChannel(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 channel_label: str = 'GFP',
                 **kwargs):
        """
        This InputOutputProcess will append the global field power (standard deviation across all channels)
        Lehmann, D., and W. Skrandies. 1980. “Reference-Free Identification of Components of Checkerboard-Evoked
        Multichannel Potential Fields.” Electroencephalography and Clinical Neurophysiology 48 (6): 609–21.
        https://doi.org/10.1016/0013-4694(80)90419-8.
        :param input_process: InputOutputProcess Class
        :param channel_label: name of new channel in layout
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(AppendGFPChannel, self).__init__(input_process=input_process, **kwargs)
        self.channel_label = channel_label

    def transform_data(self):
        data = self.input_node.data
        weights = self.input_node.w
        original_ndim = data.ndim
        # if data is an average rather than single epochs we add an extra dimension
        if original_ndim == 2:
            data = data[:, :, None]
            weights = np.ones(data.shape) * u.dimensionless_unscaled
        if weights is None:
            weights = np.ones(data.shape) * u.dimensionless_unscaled

        average = w_mean(data, weights=weights, keepdims=True, axis=1)
        variance = np.sum(weights * (data - average) ** 2,
                          axis=1, keepdims=True) / np.sum(weights, axis=1, keepdims=True)
        new_channel_data = np.sqrt(variance * data.shape[1])
        self.output_node.data = data
        self.output_node.append_new_channel(new_data=new_channel_data,
                                            layout_label=self.channel_label)
        if original_ndim == 2:
            self.output_node.data = np.squeeze(self.output_node.data)
        if weights is not None:
            new_w = np.ones((weights.shape[0], 1, weights.shape[2])) * weights.unit
            self.output_node.w = np.hstack((weights, new_w))
        self.output_node.statistical_tests = self.input_process.output_node.statistical_tests


class AppendChannels(InputOutputProcess):
    def __init__(self, new_data: type(np.array) | None = None,
                 channel_labels: List[str] | None = None,
                 **kwargs):
        """
        This InputOutputProcess will append the global field power (standard deviation across all channels)
        :param input_process: InputOutputProcess Class
        :param channel_label: name of new channel in layout
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(AppendGFPChannel, self).__init__(input_process=None, **kwargs)
        self.channel_labels = channel_labels
        self.new_data = new_data

    def transform_data(self):
        data = self.input_node.data
        assert data.shape[0] == self.new_data.shape[0]
        assert len(self.channel_labels) == self.new_data.shape[1]
        self.output_node.data = data
        for _data, channel in zip(self.new_data, self.channel_labels):
            self.output_node.append_new_channel(new_data=self.new_data,
                                                layout_label=self.channel_labels)


class CombineChannels(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 new_channel_label: str | None = None,
                 channel_labels: List[str] | None = None,
                 function: object = np.mean,
                 **kwargs):
        """
        This InputOutputProcess will append a new channel based on an operational function passed and applied to a
        subset of existing channels
        :param input_process: InputOutputProcess Class
        :param channel_labels: name of channels that will be used to apply the passed function
        :param new_channel_label: the name of the new channel
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(CombineChannels, self).__init__(input_process=input_process, **kwargs)
        self.channel_labels = channel_labels
        self.new_channel_label = new_channel_label
        self.function = function

    def transform_data(self):
        data = self.input_node.data
        _idx_ch = self.input_node.get_channel_idx_by_label(self.channel_labels)
        _new_channel_label = self.new_channel_label
        if _new_channel_label is None:
            _new_channel_label = '_'.join([_l for _l in self.channel_labels])

        # if data is an average rather than single epochs we add an extra dimension
        weights = self.input_node.w
        original_ndim = data.ndim
        # if data is an average rather than single epochs we add an extra dimension
        if original_ndim == 2:
            data = data[:, :, None]
            weights = np.ones(data.shape) * u.dimensionless_unscaled
        if weights is None:
            weights = np.ones(data.shape) * u.dimensionless_unscaled

        new_channel_data = self.function(data[:, _idx_ch, :])
        self.output_node.data = data
        self.output_node.append_new_channel(new_data=new_channel_data,
                                            layout_label=_new_channel_label)
        if original_ndim == 2:
            self.output_node.data = np.squeeze(self.output_node.data)
        if weights is not None:
            new_w = np.ones((weights.shape[0], 1, weights.shape[2])) * weights.unit
            self.output_node.w = np.hstack((weights, new_w))
        self.output_node.statistical_tests = self.input_process.output_node.statistical_tests
