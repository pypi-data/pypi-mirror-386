import json
from io import open
from peegy.io.storage.data_storage_tools import MeasurementInformation
from peegy.definitions.eeg_definitions import signal_information
from peegy.io.eeg import reader
from peegy.processing.tools.detection.definitions import TimePeakWindow, PeakToPeakMeasure, TimeROI
import os
import numpy as np
from os.path import basename
from prettytable import PrettyTable
from peegy.processing.events import event_tools
import logging
from pathlib import Path
from itertools import compress
import glob
import csv
from itertools import chain
import pandas as pd
from collections.abc import MutableMapping
import astropy.units as u
from typing import List


def flatten_dictionary(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten_dictionary(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            if np.any([isinstance(_v, MutableMapping) for _v in v]):
                for _i, _v in enumerate(v):
                    extra_sep = '' if len(v) == 1 else sep + str(_i)
                    if isinstance(_v, MutableMapping):
                        items.extend(flatten_dictionary(_v, new_key + extra_sep, sep=sep).items())
                    else:
                        items.append((new_key, _v))
            else:
                if len(v) == 1:
                    items.append((new_key, v[0]))
                else:
                    items.append((new_key, v))
        else:
            items.append((new_key, v))
    return dict(items)


class DataLinks(object):
    """
    This class is used to link the parameters associated to each data file as well as the initial and end times to
    to be read
    """

    def __init__(self,
                 parameters: dict = {},
                 parameters_file: str | None = None,
                 parameters_date: str = '',
                 data_file: str | None = None,
                 data_header: object | None = None,
                 data_date: str = '',
                 ini_time=0.0,
                 end_time=None,
                 meta_data: list = [],
                 label: str | None = None):
        self.parameters_file = parameters_file
        self.parameters_date = parameters_date
        self.data_file = data_file
        self.data_date = data_date
        self.data_header = data_header
        self.ini_time = ini_time
        self.end_time = end_time
        self.measurement_parameters = parameters
        self.meta_data = meta_data
        self.label = label


def match_keywords(key_words: List[str] | None = None, word: str | None = None, deep_match=False):
    """
    This function matches a list of keywords in an string.
    :param key_words: string list of key words to be matched
    :param word: string variable where words are to be found
    :param deep_match: if True, all keywords must be present to return True
    :return: Bool variable indicating if a match was obtained
    """
    _found = False
    if deep_match:
        if key_words is not None and np.all([_key_word in word for _key_word in key_words]):
            _found = True
    else:
        if key_words is not None and any(
                [_key_word in word for _key_word in key_words]):
            _found = True
    return _found


def parse_processing_chain(file_path=''):
    with open(file_path, encoding="utf-8") as f:
        chain = json.load(f)
    all_keys = list(chain.keys())
    if 'measurements' not in all_keys:
        return
    # get default values
    defaults_list = []
    if 'defaults' in all_keys:
        defaults_list = chain['defaults']
    print(defaults_list)
    # set defaults
    out_measurements = []
    # add any default value not present in the read measurement
    template = {}
    if defaults_list:
        template = defaults_list.copy()

    for _c_measurement in chain['measurements']:
        _c_dict = template.copy()
        _signals = []
        _time_peaks = []
        _peak_to_peak_amps = []
        _measurement_info = []
        _roi_windows = []
        # add default items if they are not part of the measurement
        for _items, _val in template.items():
            if _items not in list(_c_measurement.keys()):
                _c_measurement[_items] = _val
        for _idx_item, (_field, _value) in enumerate(_c_measurement.items()):
            if _field == 'measurement_info':
                if 'measurement_info' in list(_c_dict.keys()):
                    if len(_c_dict['measurement_info']) > len(_c_measurement['measurement_info']) == 1:
                        for _c_m in _c_dict['measurement_info']:
                            _measurement_info.append(
                                MeasurementInformation(**modify_template(_c_m, _c_measurement['measurement_info'][0])))
                    elif len(_c_dict['measurement_info']) == len(_c_measurement['measurement_info']):
                        for _m_idx, _c_m in enumerate(_c_dict['measurement_info']):
                            _measurement_info.append(
                                MeasurementInformation(
                                    **modify_template(_c_m, _c_measurement['measurement_info'][_m_idx])))
                    else:
                        print('The number of measurement_info must be 1 or the same as in the template')
                else:
                    for _measure in _value:
                        _measurement_info.append(MeasurementInformation(**_measure))
                _c_dict['measurement_info'] = _measurement_info
            elif _field == 'roi_windows':
                for _roi in _value:
                    if not isinstance(_roi['measure'], list):
                        _roi['measure'] = [_roi['measure']]
                    if not isinstance(_roi['label'], list):
                        _roi['label'] = [_roi['label']]
                    assert len(_roi['label']) == len(_roi['measure'])

                    for _m, _lab in zip(_roi['measure'], _roi['label']):
                        _c_roi = _roi.copy()
                        _c_roi['measure'] = _m
                        _c_roi['label'] = _lab
                        _roi_windows.append(TimeROI(**_c_roi))
                _c_dict['roi_windows'] = _roi_windows
            elif _field == 'signal_info':
                for _signal in _value:
                    if 'signal_info' in list(_c_dict.keys()):
                        if isinstance(_c_dict['signal_info'], list):
                            for _s in _c_dict['signal_info']:
                                _signals.append(signal_information(**modify_template(_s, _signal)))
                        else:
                            _signals.append(signal_information(**modify_template(_c_dict['signal_info'], _signal)))
                    else:
                        _signals.append(signal_information(**_signal))
                _c_dict[_field] = _signals
            elif _field == 'peak_time_windows':
                for _time_peak in _value:
                    _time_peaks.append(TimePeakWindow(**_time_peak))
                _c_dict[_field] = _time_peaks
            elif _field == 'peak_to_peak_amp_labels':
                for _peak_amp in _value:
                    _peak_to_peak_amps.append(PeakToPeakMeasure(**_peak_amp))
                _c_dict[_field] = _peak_to_peak_amps
            elif _field == 'data_files':
                _data_path = os.path.dirname(_value[0])
                _c_dict['path'] = _data_path
                _c_dict[_field] = _value
            else:
                _c_dict[_field] = _value
        # convert numeric array to numpy array
        convert_dict_to_numpy(_c_dict)
        out_measurements.append(_c_dict)
    return out_measurements


def modify_template(template={}, update_dict={}):
    out_dict = template.copy()
    for _key, _value in list(update_dict.items()):
        out_dict[_key] = _value
    return out_dict


def convert_dict_to_numpy(_dict={}):
    for _field, _value in _dict.items():
        if isinstance(_value, list):
            _dict[_field] = np.array(_value)
        if isinstance(_value, dict):
            convert_dict_to_numpy(_dict[_field])


def get_files_and_meta_files(measurement_path: str = '',
                             filter_key_words_in_path: List[str] | None = None,
                             exclude_key_words_in_path: List[str] | None = None,
                             filter_key_words_in_file: List[str] | None = None,
                             exclude_key_words_in_file: List[str] | None = None,
                             deep_match_in_filter_path: bool = True,
                             deep_match_in_filter_file: bool = True,
                             deep_match_in_exclude_path: bool = True,
                             deep_match_in_exclude_file: bool = True,
                             ignore_meta_file=False,
                             file_types: List[str] = ['bdf', 'edf'],
                             meta_file_extension: str = 'json',
                             split_trigger_codes: List[float] | None = None,
                             ) -> pd.DataFrame:
    """
    This function search for files which extension is defined by file_types and meta_files associated to each file.
    Each file will be associated to the meta_file in the output dataframe.
    This is, in order to pair a bdf to json file both should have the same name.
    The result is a list of DataLinks object, containing the information that links both files.
    If the meta_file_type is a json file, the json file will be parsed as a dictionary in the DataLinks parameters and
    also in the output dataframe. In this way, the data to be processed can be manipulated using pandas
    functionalities.
    :param measurement_path: the root path to search for pairs of files
    :param filter_key_words_in_path: if provided, the return list will only contain DataLinks object whose paths does
    include
    the exclude_key_words_in_path. This is useful to process entire folders with different conditions
    :param exclude_key_words_in_path: if provided, the return list will only contain DataLinks object whose paths does
     not include
    the exclude_key_words_in_path. This is useful to process entire folders with different conditions
    :param filter_key_words_in_file: if provided, the return list will only contain DataLinks object whose file name
     does include
    the filter_key_words_in_file. This is useful to process entire folders with different conditions
    :param exclude_key_words_in_file: if provided, the return list will only contain DataLinks object whose file name
    does not include
    the exclude_key_words_in_path. This is useful to process entire folders with different conditions
    :param deep_match_in_filter_path: if True, all keywords must be present to return True
    :param deep_match_in_filter_file: if True, all keywords must be present to return True
    :param deep_match_in_exclude_path: if True, all keywords must be present to return True
    :param deep_match_in_exclude_file: if True, all keywords must be present to return True
    :param meta_file_extension: if True it will not care whether json file is present or not
    :param file_types: a list of strings indicating the file types to be found, e.g. .bdf, .edf, .txt, .json, etcetera
    :param split_trigger_codes: list of trigger codes. If provided, the bdf file will be marked in chunks starting at
    each of these trigger events.
    The time stamps indicating the beginning and end of eeach block will be passed in  time the ini_time and
    end_time of the DataLinks class.
    :return: a Pandas data frame with DataLinks objects which contain the information linking the files
    """
    data_files = []
    for files in file_types:
        data_files.extend(sorted(Path(measurement_path).glob('**/*.{:}'.format(files))))

    # avoid hidden folders
    _to_keep = []
    for _file in data_files:
        _to_keep.append(any([_parts.startswith('.') for _parts in os.path.normpath(str(_file)).split(os.sep)]) is False)
    data_files = list(compress(data_files, _to_keep))

    par_out = pd.DataFrame()
    for i, _full_file_name in enumerate(data_files):
        _data_file_name = _full_file_name.stem
        _meta_file_path = ''

        if meta_file_extension:
            _meta_file_path = _full_file_name.parent.joinpath(_data_file_name + '.{:}'.format(meta_file_extension))
            _meta_file_name = _data_file_name + '.{:}'.format(meta_file_extension)
        if filter_key_words_in_path is not None and not match_keywords(
                filter_key_words_in_path, str(_full_file_name),
                deep_match=deep_match_in_filter_path):
            continue
        if exclude_key_words_in_path is not None and match_keywords(
                exclude_key_words_in_path, str(_full_file_name),
                deep_match=deep_match_in_exclude_path):
            continue

        if filter_key_words_in_file is not None and \
                not (match_keywords(filter_key_words_in_file, _data_file_name, deep_match=deep_match_in_filter_file) and
                     match_keywords(filter_key_words_in_file, _meta_file_name, deep_match=deep_match_in_filter_file)):
            continue
        if exclude_key_words_in_file is not None and \
                (match_keywords(exclude_key_words_in_file, _data_file_name, deep_match=deep_match_in_exclude_file) or
                 match_keywords(exclude_key_words_in_file, _meta_file_name, deep_match=deep_match_in_exclude_file)):
            continue

        _parameters = {}

        if not ignore_meta_file and os.path.isfile(_meta_file_path) and meta_file_extension == 'json':
            with open(_meta_file_path, 'r') as f:
                try:
                    _parameters = json.load(f)
                except ValueError:
                    print('could not open {:}'.format(_meta_file_path))

        if split_trigger_codes is not None:
            _data = reader.eeg_reader(_full_file_name)
            raw_events = _data.get_events()
            events = event_tools.detect_events(event_channel=raw_events, fs=_data.fs)
            print(event_tools.Events(events=events).summary())
            _split_events = np.array([_e for _e in events if _e.code in split_trigger_codes])
            ini_time = [_e.time_pos for _e in _split_events]
            end_time = [_e.time_pos for _e in _split_events[1:]]
            end_time.append(None)
            split_codes = [_e.code for _e in _split_events]
        else:
            ini_time = [0 * u.s]
            end_time = [None]
            split_codes = [None]

        for _ini_time, _end_time, _code in zip(ini_time, end_time, split_codes):
            data_links = DataLinks(parameters=_parameters,
                                   parameters_file=_meta_file_path,
                                   data_file=_full_file_name,
                                   ini_time=_ini_time,
                                   end_time=_end_time,
                                   label=_code
                                   )

            par_out = pd.concat([par_out, pd.DataFrame.from_dict(
                dict({k: [v] for k, v in _parameters.items()},
                     **{'data_links': [data_links]}))],
                                ignore_index=True)
    if par_out.size:
        t = PrettyTable()
        _aux = par_out.data_links.values.astype(np.ndarray)
        t.add_column(fieldname='File name', column=[basename(x.parameters_file) for x in _aux])
        t.add_column(fieldname='File date', column=[basename(x.parameters_date) for x in _aux])
        t.add_column(fieldname='data file name', column=[basename(x.data_file) for x in _aux])
        t.add_column(fieldname='data file date', column=[x.data_date for x in _aux])
        t.add_column(fieldname='Code', column=[x.label for x in _aux])
        t.add_column(fieldname='Ini time', column=[x.ini_time for x in _aux])
        t.add_column(fieldname='End time', column=[x.end_time for x in _aux])
        logging.info(t)
        print(t)
    else:
        print('No files were found')
    return par_out


def get_data_and_meta_data_files(measurement_path: str = '',
                                 filter_key_words_in_path: List[str] | None = None,
                                 exclude_key_words_in_path: List[str] | None = None,
                                 filter_key_words_in_file: List[str] | None = None,
                                 exclude_key_words_in_file: List[str] | None = None,
                                 deep_match_in_filter_path: bool = True,
                                 deep_match_in_filter_file: bool = True,
                                 deep_match_in_exclude_path: bool = True,
                                 deep_match_in_exclude_file: bool = True,
                                 meta_data_file_extension: List[str] = ['.json'],
                                 rows_to_skip=0,
                                 ) -> [DataLinks]:
    """
    This function search for .bdf or .edf  and .json files recursively and pair them according to name.
    This is, in order to pair a bdf to json file both should have at least the same name (it may be longer).
    The result is a list of DataLinks object, containing the information that links both files.
    :param measurement_path: the root path to search for pairs of files
    :param filter_key_words_in_path: if provided, the return list will only contain DataLinks object whose paths does
     include
    the exclude_key_words_in_path. This is useful to process entire folders with different conditions
    :param exclude_key_words_in_path: if provided, the return list will only contain DataLinks object whose paths does
    not include
    the exclude_key_words_in_path. This is useful to process entire folders with different conditions
    :param filter_key_words_in_file: if provided, the return list will only contain DataLinks object whose file name
    does include
    the filter_key_words_in_file. This is useful to process entire folders with different conditions
    :param exclude_key_words_in_file: if provided, the return list will only contain DataLinks object whose file name
    does not include
    the exclude_key_words_in_path. This is useful to process entire folders with different conditions
    :param deep_match_in_filter_path: if True, all keywords must be present to return True
    :param deep_match_in_filter_file: if True, all keywords must be present to return True
    :param deep_match_in_exclude_path: if True, all keywords must be present to return True
    :param deep_match_in_exclude_file: if True, all keywords must be present to return True
    :param meta_data_file_extension: list indicating the extension of associated meta_data files, e.g. ['.csv', .'json']
    :param rows_to_skip: number of rows to skip when reading csv file
    :return: a list of DataLinks objects which contain the information linking .bdf or .edf and .json files
    """
    types = ('**/*.bdf', '**/*.edf')  # the tuple of file types
    data_files = []
    for files in types:
        data_files.extend(sorted(Path(measurement_path).glob(files)))

    par_out = []
    for i, _full_file_name in enumerate(data_files):
        _data_file_name, _file_extension = os.path.splitext(_full_file_name)
        if filter_key_words_in_path is not None and not match_keywords(
                filter_key_words_in_path, str(_full_file_name),
                deep_match=deep_match_in_filter_path):
            continue
        if exclude_key_words_in_path is not None and match_keywords(
                exclude_key_words_in_path, str(_full_file_name),
                deep_match=deep_match_in_exclude_path):
            continue

        if filter_key_words_in_file is not None and not (
                match_keywords(filter_key_words_in_file, _data_file_name, deep_match=deep_match_in_filter_file)):
            continue
        if exclude_key_words_in_file is not None and (
                match_keywords(exclude_key_words_in_file, _data_file_name, deep_match=deep_match_in_exclude_file)):
            continue

        meta_files = list(chain(*[sorted(glob.glob(_data_file_name + '*{:}'.format(_extension)))
                                  for _extension in meta_data_file_extension]))
        meta_data = []
        for _meta_file in meta_files:
            _meta_file_name, file_extension = os.path.splitext(_meta_file)
            if filter_key_words_in_file is not None and not (
                    match_keywords(filter_key_words_in_file, _meta_file_name, deep_match=deep_match_in_filter_file)):
                continue
            if exclude_key_words_in_file is not None and (
                    match_keywords(exclude_key_words_in_file, _meta_file_name, deep_match=deep_match_in_exclude_file)):
                continue
            if file_extension == '.json':
                with open(_meta_file, 'r') as f:
                    meta_data.append(json.load(f))
            columns = []
            if file_extension == '.csv':
                with open(_meta_file, 'r') as f:
                    reader = csv.reader(f)
                    for _i_r, row in enumerate(reader):
                        if _i_r < rows_to_skip:
                            continue
                        if _i_r == rows_to_skip:
                            # first row
                            columns_names = [[value] for value in row]
                            columns = [[np.array([])] * len(columns_names)]
                            continue

                        for _c, value in enumerate(row):
                            columns[0][_c] = np.append(columns[0][_c], value)
                    current_meta_data = dict()
                    for _col_idx, _col_name in enumerate(columns_names):
                        current_meta_data[_col_name[0]] = columns[0][_col_idx]
                    meta_data.append(current_meta_data)

        data_links = DataLinks(parameters=meta_data,
                               parameters_file=_meta_file,
                               data_file=_full_file_name,
                               )
        par_out.append(data_links)

    t = PrettyTable()
    t.add_column(fieldname='File name', column=[basename(x.parameters_file) for x in par_out])
    t.add_column(fieldname='File date', column=[basename(x.parameters_date) for x in par_out])
    t.add_column(fieldname='bdf file name', column=[basename(x.data_file) for x in par_out])
    t.add_column(fieldname='bdf file date', column=[x.data_date for x in par_out])
    logging.info(t)
    print(t)
    return par_out
