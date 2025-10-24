import calendar
import os
from collections import defaultdict
from datetime import datetime, timedelta
from itertools import groupby
from pathlib import Path
from typing import Optional, Callable

import numpy as np

from uhslc_station_tools import filtering as filt
from uhslc_station_tools import utils
from uhslc_station_tools.utils import get_missing_months, datenum


class Sensor:
    """
    A single physical/virtual sensor and its time series payload.

    Attributes:
        rate: Sampling interval in minutes.
        height: Reference/switch height associated with the sensor.
        type: Short channel/sensor code (e.g., ``"PRS"``, ``"RAD"``).
        date: Numpy ``datetime64`` of the first sample.
        data: 2-D array of samples (rows correspond to line groups in monp format).
        time_info: Per-row time info strings (legacy header-like prefixes).
        header: Raw monp header line for this sensor.
    """

    def __init__(self, rate: int, height: int, sensor_type: str, date: str, data: [int], time_info: str, header: str):
        """
        Initialize a :class:`Sensor`.

        Args:
            rate: Sampling interval in minutes.
            height: Reference/switch height.
            sensor_type: Short sensor code (e.g., ``"PRS"``).
            date: Initial timestamp (usually ``numpy.datetime64``-compatible string).
            data: 2-D array-like of sea-level measurements.
            time_info: List-like of time-info strings per data row.
            header: Original header string for this sensor, as parsed from file.
        """

        self.rate = rate
        self.height = height
        self.type = sensor_type
        self.date = date
        self.data = data
        self.time_info = time_info
        self.header = header

    def get_flat_data(self):
        """
        Return the sensor's data flattened to 1-D.

        Returns:
            ``numpy.ndarray`` of shape ``(N,)`` with samples in row-major order.
        """

        return self.data.flatten()

    def get_time_vector(self):
        """
        Build a vector of timestamps for each flattened sample.

        The vector starts at ``self.date`` and advances by ``self.rate`` minutes
        per element to match :meth:`get_flat_data`.

        Returns:
            ``numpy.ndarray`` of ``datetime64[m]`` timestamps with length equal to
            the flattened data size.
        """

        return np.array(
            [self.date + np.timedelta64(i * int(self.rate), 'm') for i in range(self.get_flat_data().size)])

    def update_header_ref(self, reference_level):
        """
        Update the sensor header's ``REF=`` field with a new reference level.

        Args:
            reference_level: New integer reference height.

        Returns:
            The updated header string with the new reference inserted.
        """

        new_header = self.header[:60] + '{:04d}'.format(reference_level) + self.header[64:]
        self.header = new_header

        return self.header

    def get_reference_difference(self, new_reference):
        """
        Compute the offset between a new reference and the current one.

        Args:
            new_reference: Proposed reference height.

        Returns:
            Integer difference ``new_reference - self.height``.
        """

        diff = new_reference - self.height

        return diff

    def set_reference_height(self, new_reference):
        """
        Set the sensor's reference height in-place.

        Args:
            new_reference: New integer reference height.
        """

        self.height = new_reference

    def __repr__(self):
        """
        Return the sensor type for readable debugging/printing.
        """

        return self.type


class SensorCollection:
    """
    Dictionary-like container of :class:`Sensor` objects keyed by type code.
    """

    def __init__(self, sensors: Sensor = None):
        """
        Initialize an empty or pre-populated sensor mapping.

        Args:
            sensors: Optional initial mapping ``{type: Sensor}``. If ``None``, an
                empty dict is created.
        """

        if sensors is None:
            sensors = {}

        self.sensors = sensors

    def add_sensor(self, sensor: Sensor):
        """
        Add or replace a sensor under its ``sensor.type`` key.

        Args:
            sensor: Sensor instance to insert.
        """

        self.sensors[sensor.type] = sensor

    def __getitem__(self, name):
        """
        Return the sensor with key ``name``.
        """

        return self.sensors[name]

    def __iter__(self):
        """
        Iterate sensor keys in insertion order (like ``dict``).
        """

        return iter(self.sensors)

    def keys(self):
        """
        Keys view of the underlying mapping.
        """

        return self.sensors.keys()

    def items(self):
        """
        Items view (``(key, Sensor)`` pairs).
        """

        return self.sensors.items()

    def values(self):
        """
        Values view of :class:`Sensor` objects.
        """

        return self.sensors.values()


class Month:
    """
    One month of data for a single station.

    Attributes:
        month: Month integer ``1-12``.
        year: Four-digit year.
        name: Abbreviated month name (e.g., ``"Jan"``).
        sensor_collection: :class:`SensorCollection` for this month.
        station_id: Station numeric/string identifier used in filenames.
        day_count: Number of days in the month.
    """

    def __init__(self, month: int, year: int, sensors: SensorCollection, st_id: str):
        """
        Initialize a :class:`Month`.

        Args:
            month: Month number ``1-12``.
            year: Four-digit year.
            sensors: Sensors observed during this month.
            st_id: Station identifier used in file naming.
        """

        self.month = month
        self.year = year
        self.name = calendar.month_abbr[month]
        self.sensor_collection = sensors
        self.station_id = st_id
        self.day_count = calendar.monthrange(year, month)[1]

    def assemble_root_filename(self, four_digit_year=False):
        """
        Return the base ``<station><YY><MM>`` (or ``<station><YYYY><MM>``) name.

        Args:
            four_digit_year: If ``True``, use ``YYYY``; otherwise use ``YY``.

        Returns:
            Root filename stem without prefix/suffix.
        """

        month_int = self.month
        month_str = "{:02}".format(month_int)
        if not four_digit_year:
            year_str = str(self.year)[2:]
        else:
            year_str = str(self.year)
        station_num = self.station_id
        root_filename = '{}{}{}'.format(station_num, year_str, month_str)

        return root_filename

    def get_ts_filename(self):
        """
        Return the ``t<station><YY><MM>.dat`` filename as :class:`Path`.
        """

        file_name = '{}{}{}'.format('t', self.assemble_root_filename(), '.dat')

        return Path(file_name)

    def get_mat_filename(self):
        """
        Return a mapping of sensor key -> high-frequency ``.mat`` filename.

        Returns:
            Dict mapping each sensor key (e.g., ``"PRS"``) to a filename like
            ``t<station><YYYY><MM><sensor>.mat``.
        """

        sensor_file = {}
        for key, sensor in self.sensor_collection.items():
            file_name = 't{}{}{}'.format(self.assemble_root_filename(four_digit_year=True), key.lower(), '.mat')
            sensor_file[key] = file_name

        return sensor_file

    def get_save_folder(self):
        """
        Return ``t<station>`` folder name used for outputs.
        """

        return '{}{}'.format('t', self.station_id)


# It should be like this: Each Station has a Month/Months associated with it, and then each Month has one or more
# Sensors. This way we can account for removal/addition of sensors between months.
# I've been going a lot back and forth between whether Station should have Months or whether the Month should have
# one Station. The right approach seems to be that each Station can have one or multiple months loaded with it,
# and each month has its own Sensors with their own data.

class Station:
    """
    A multi-month container for one station with I/O helpers.

    Attributes:
        name: Station short name/alias.
        location: ``[lat, lon]`` in decimal degrees.
        month_collection: List of :class:`Month` objects loaded for the station.
        aggregate_months: Combined arrays across months for quick access.
        top_level_folder: Optional override for the export root path.
        year_range: Sorted list of years covered by ``month_collection``.
    """

    def __init__(self, name: str, location: [float, float], month: [Month]):
        """
        Initialize a :class:`Station` from one or more months.

        Args:
            name: Station name.
            location: Latitude/longitude pair.
            month: Iterable of :class:`Month` instances.
        """

        self.name = name
        self.location = location
        self.month_collection = month
        self.aggregate_months = self.combine_months()
        self.top_level_folder = None
        self.year_range = sorted(set([m.year for m in month]))

    def datenum_to_datetime(self, dn):
        """
        Convert MATLAB-style ``datenum`` (float) to :class:`datetime`.

        Args:
            dn: MATLAB datenum (days since year 0, with fractional day).

        Returns:
            Python ``datetime`` representing the same instant.
        """

        days = int(dn) - 366  # because MATLAB datenum starts at year 0, Python at 1
        frac = dn % 1

        return datetime.fromordinal(days) + timedelta(days=frac)

    def get_target_month_range(self, target_start_yyyymm, target_end_yyyymm):
        """
        Compute (start, end) datetimes for inclusive month range.

        Args:
            target_start_yyyymm: Start in ``YYYYMM`` format.
            target_end_yyyymm: End in ``YYYYMM`` format (inclusive on months).

        Returns:
            Tuple ``(start_dt, end_dt)`` where ``end_dt`` is the first day of the
            month after the target end.
        """

        start_year = target_start_yyyymm // 100
        start_month = target_start_yyyymm % 100
        target_start_time = datetime(start_year, start_month, 1)
        end_year = target_end_yyyymm // 100
        end_month = target_end_yyyymm % 100

        if end_month == 12:
            target_end_time = datetime(end_year + 1, 1, 1)
        else:
            target_end_time = datetime(end_year, end_month + 1, 1)

        return target_start_time, target_end_time

    def month_length(self):
        """
        Return the number of months loaded for this station.
        """

        return len(self.month_collection)

    def combine_months(self):
        """
        Concatenate per-sensor data and times across all months.

        For each sensor key present in any month, this function stacks the
        flattened data and corresponding timestamps in time order and also
        computes/aggregates outlier indices per sensor.

        Returns:
            Dict with keys ``data`` (mapping sensor->1D array), ``time`` (mapping
            sensor->1D time array), and ``outliers`` (mapping sensor->indices).
        """

        combined_sealevel_data = {}
        comb_time_vector = {}
        sensor_outliers = {}
        offsets = {}  # keeps track of cumulative data length per sensor

        for i, _month in enumerate(self.month_collection):
            for key, value in _month.sensor_collection.sensors.items():
                if 'ALL' not in key:
                    flat_data = _month.sensor_collection.sensors[key].get_flat_data()
                    time = _month.sensor_collection.sensors[key].get_time_vector()
                    rate = _month.sensor_collection.sensors[key].rate  # sampling freq str
                    # accumulate all the data for each sensor for all months
                    # by creating extending/concatenating the arrays
                    if key in combined_sealevel_data:
                        combined_sealevel_data[key] = np.concatenate(
                            (combined_sealevel_data[key], flat_data), axis=0)
                        if i > 0:
                            try:
                                prev_sensor = self.month_collection[i - 1].sensor_collection.sensors[key]
                                offsets[key] += len(prev_sensor.get_flat_data())
                            except KeyError:
                                # Sensor was not present in previous month - do nothing.
                                pass
                            except Exception as e:
                                print(f"WARNING: Could not get offset for sensor '{key}' in month index {i-1}: {e}")
                                offsets[key] = offsets.get(key, 0)
                        # indices of all outliers
                        outliers_tuple = (np.sort(np.concatenate((sensor_outliers[key],
                                                                  utils.find_outliers(time, flat_data, rate,
                                                                                      offsets[key])[0]), axis=0)))
                        sensor_outliers[key] = outliers_tuple
                    else:
                        combined_sealevel_data[key] = flat_data
                        sensor_outliers[key] = utils.find_outliers(time, flat_data, rate)[0]
                        offsets[key] = 0
                if 'ALL' not in key:
                    if key in comb_time_vector:
                        comb_time_vector[key] = np.concatenate((comb_time_vector[key], time), axis=0)
                    else:
                        comb_time_vector[key] = time
        combined = {'data': combined_sealevel_data, 'time': comb_time_vector, 'outliers': sensor_outliers}

        return combined

    def back_propagate_changes(self, combined_data):
        """
        Write changes from combined arrays back into monthly matrices. Because we combine 
        multiple months of data, we need the ability to split the data back to individual 
        months as we are making changes to data (during cleaning) and we need to save those 
        changes.

        Args:
            combined_data: Mapping ``{sensor: 1D array}`` containing updated
                flattened values for each sensor as returned by
                :meth:`combine_months`.
        """

        so_far_index = {}  # Keeps track of data sizes for each sensor for each month so that we can separate it
        # properly by each month
        for i, _month in enumerate(self.month_collection):
            for key, value in _month.sensor_collection.sensors.items():
                if 'ALL' not in key:
                    # We need to keep track of the previous data size so we can slide the index for each new month
                    if key in combined_data:
                        if i == 0:
                            so_far_index[key] = 0
                        else:
                            try:
                                previous_data_size = self.month_collection[i - 1].sensor_collection.sensors[key].data.size
                                so_far_index[key] = so_far_index[key] + previous_data_size
                            except KeyError:
                                # Sensor was not present in the previous month - just carry forward current offset.
                                so_far_index[key] = so_far_index.get(key, 0)
                            except Exception as e:
                                print(f"WARNING: Failed to retrieve previous data size for sensor '{key}' at month index {i-1}: {e}")
                                so_far_index[key] = so_far_index.get(key, 0)
                        data_size = _month.sensor_collection.sensors[key].data.size
                        data_shape = _month.sensor_collection.sensors[key].data.shape
                        try:
                            _month.sensor_collection.sensors[key].data = np.reshape(
                                combined_data[key][so_far_index[key]:data_size + so_far_index[key]],
                                data_shape)
                        except ValueError as e:
                            print(e, "i: {}, month: {}, sensor:{}".format(i, _month.month, key))

    def all_equal(self, iterable):
        """
        Return ``True`` if all elements of ``iterable`` are equal.
        """

        g = groupby(iterable)

        return next(g, True) and not next(g, False)

    def get_sampling_rates(self):
        """
        Check whether each sensor's rate is constant across months.

        Returns:
            Dict mapping ``sensor_key -> bool`` indicating if all monthly rates
            match for that sensor.
        """

        # Collect all rates for each sensor for all months.
        rates = defaultdict(list)
        for month in self.month_collection:
            for key, sensor in month.sensor_collection.sensors.items():
                if key != "ALL":
                    rates[key].append(sensor.rate)

        # Check if rates for each sensor are equal.
        result = {}
        for sensor, rate in rates.items():
            result[sensor] = self.all_equal(rate)

        return result

    def is_sampling_inconsistent(self):
        """
        Return ``True`` if any sensor has inconsistent rates across months.
        """

        return False in self.get_sampling_rates().values()

    def update_header_reference_level(self, date, new_level, sens):
        """
        Update reference level in headers for months at/after a given date.

        Args:
            date: An object exposing ``year()`` and ``month()`` used for
                comparison to sensor dates (e.g., ``QtCore.QDate``).
            new_level: New integer reference level to write.
            sens: Sensor key to update (e.g., ``"PRS"``).

        Returns:
            Tuple ``(months_updated, ref_diff, new_header)`` describing how many
            months were changed and returning the last computed difference and
            header string.
        """

        months_updated = 0
        for month in self.month_collection:
            # Todo: This should catch all months, even if the loaded months wrap into a new
            #  year, ie. we loaded month 11, 12, 1. But write a test for it
            if month.month >= date.month() or month.sensor_collection[sens].date.astype(
                    object).year > date.year():
                months_updated += 1
                ref_diff = month.sensor_collection.sensors[sens].get_reference_difference(new_level)
                new_header = month.sensor_collection.sensors[sens].update_header_ref(new_level)
                month.sensor_collection.sensors[sens].set_reference_height(new_level)

        return months_updated, ref_diff, new_header

    def assemble_ts_text(self):
        """
        Assemble monp-format text lines for all months and sensors.

        This converts in-memory arrays into the fixed-width legacy ``.dat``
        representation, placing PRD lines first and appending end-of-channel
        sentinels (``80*'9'``).

        Returns:
            List ``[[month_obj, lines], ...]`` where ``lines`` is a list of
            strings ready to be written to a file.
        """

        months = []
        for month in self.month_collection:
            prd_text = []
            others_text = []
            for key, sensor in month.sensor_collection.items():
                if key == "ALL":
                    continue
                id_sens = month.station_id + key
                id_sens = id_sens.rjust(8, ' ')
                year = str(sensor.date.astype(object).year)[-2:]
                year = year.rjust(4, ' ')
                m = "{:2}".format(sensor.date.astype(object).month)
                # day = "{:3}".format(sensor.date.astype(object).day)

                # To get the line counter, it is 60 minutes per hour x 24 hours in a day divided by data points
                # per row which can be obtained from .data.shape, and divided by the sampling rate. The number
                # given by that calculation tells after how many rows to reset the counter, that is how many rows of
                # data per day. This is true for all sensors besides PRD. PRD shows the actual hours (increments of
                # 3 per row)
                # TODO: ask Fee if there are any other sensors that have 15 minute sampling rate and check the
                # monp file if there is
                if key == "PRD":
                    line_count_multiplier = 3
                    prd_text.append(sensor.header)
                else:
                    line_count_multiplier = 1
                    others_text.append(sensor.header)
                for row, data_line in enumerate(sensor.data):
                    rows_per_day = 24 * 60 // sensor.data.shape[1] // int(sensor.rate)
                    line_num = (row % rows_per_day) * line_count_multiplier
                    day = 1 + (row // rows_per_day)
                    day = "{:3}".format(day)
                    line_num = "{:3}".format(line_num)
                    nan_ind = np.argwhere(np.isnan(data_line))
                    data_line[nan_ind] = 9999
                    sl_round_up = np.round(data_line).astype(
                        int)  # round up sealevel data and convert to int

                    # right justify with 5 spaces
                    spaces = 4
                    if int(sensor.rate) >= 5:
                        spaces = 5
                    data_str = ''.join([str(x).rjust(spaces, ' ') for x in sl_round_up])  # convert data to string
                    full_line_str = '{}{}{}{}{}{}'.format(id_sens, year, m, day, line_num, data_str)

                    if key == "PRD":
                        prd_text.append(full_line_str + "\n")
                    else:
                        others_text.append(full_line_str + "\n")

                # If there is data for sensor other than PRD append 9s at the nd
                if others_text:
                    others_text.append(80 * '9' + '\n')
            prd_text.append(80 * '9' + '\n')
            prd_text.extend(others_text)
            months.append([month, prd_text])

        return months

    def save_ts_files(self, text_collection, path=None, is_test_mode=False, target_start_yyyymm: Optional[int] = None, 
                      target_end_yyyymm: Optional[int] = None, callback: Callable = None):
        """
        Write legacy monp `.dat` time-series files for each month.

        If `target_start_yyyymm` and `target_end_yyyymm` are provided,
        only months within that inclusive range are written (same month-windowing as fast delivery).

        Args:
            text_collection: Output of :meth:`assemble_ts_text`.
            path: Optional parent directory for saving. If None, defaults are resolved by utils.
            is_test_mode: If True, write to a sandbox/test location.
            callback: Optional function `callback(success, failure)` invoked after writing.
            target_start_yyyymm: Inclusive start month as YYYYMM.
            target_end_yyyymm: Inclusive end month as YYYYMM.

        Returns:
            Tuple (success, failure) containing message dicts for UI use.

        Raises:
            ValueError: If only one of target_start_yyyymm or target_end_yyyymm is provided.
        """

        if (target_start_yyyymm is None) ^ (target_end_yyyymm is None):
            raise ValueError("Both target_start_yyyymm and target_end_yyyymm must be specified.")

        target_start_time = target_end_time = None
        if target_start_yyyymm is not None and target_end_yyyymm is not None:
            target_start_time, target_end_time = self.get_target_month_range(
                target_start_yyyymm, target_end_yyyymm
            )

        # Text collection here refers to multiple text files for each month loaded.
        success = []
        failure = []

        for month_obj, lines in text_collection:
            # If a target range is given, skip months outside it
            if target_start_time is not None:
                month_start = datetime(month_obj.year, month_obj.month, 1)
                if not (target_start_time <= month_start < target_end_time):
                    continue

            file_name = month_obj.get_ts_filename()
            save_folder = month_obj.get_save_folder()  # t + station_id
            save_path = utils.get_top_level_directory(parent_dir=path, is_test_mode=is_test_mode) \
                        / utils.HIGH_FREQUENCY_FOLDER / save_folder / str(month_obj.year)
            utils.create_directory_if_not_exists(save_path)

            try:
                with open(Path(save_path / file_name), 'w') as the_file:
                    for lin in lines:
                        the_file.write(lin)
                    the_file.write(80 * '9' + '\n')
                    success.append({
                        'title': "Success",
                        'message': f"Success \n{file_name} Saved to {save_path}\n"
                    })
            except IOError as e:
                failure.append({
                    'title': "Error",
                    'message': f"Cannot Save to {save_path}\n{e}\n Please select a different path to save to"
                })

        if callback:
            callback(success, failure)

        return success, failure

    def save_mat_high_fq(self, path: str, is_test_mode=False, target_start_yyyymm: Optional[int] = None,
                         target_end_yyyymm: Optional[int] = None, callback: Callable = None):
        """
        Save monthly high-frequency data to MATLAB `.mat` files.

        One file per sensor per month is written. If `target_start_yyyymm` and
        `target_end_yyyymm` are provided, only months within that inclusive range
        are written (same month-windowing as fast delivery).

        Args:
            path: Parent directory for exports.
            is_test_mode: If True, write to a sandbox/test location.
            callback: Optional function `callback(success, failure)` invoked after writing.
            target_start_yyyymm: Inclusive start month as YYYYMM.
            target_end_yyyymm: Inclusive end month as YYYYMM.

        Returns:
            Tuple (success, failure) of message dicts for UI use.

        Raises:
            ValueError: If only one of target_start_yyyymm or target_end_yyyymm is provided.
        """

        import scipy.io as sio

        if (target_start_yyyymm is None) ^ (target_end_yyyymm is None):
            raise ValueError("Both target_start_yyyymm and target_end_yyyymm must be specified.")

        # Build target window (half-open on datetime: [start, next month after end))
        target_start_time = target_end_time = None
        if target_start_yyyymm is not None and target_end_yyyymm is not None:
            target_start_time, target_end_time = self.get_target_month_range(
                target_start_yyyymm, target_end_yyyymm
            )

        success = []
        failure = []

        for month in self.month_collection:
            # If a target range is given, skip months outside it
            if target_start_time is not None:
                month_start = datetime(month.year, month.month, 1)
                if not (target_start_time <= month_start < target_end_time):
                    continue

            for key, sensor in month.sensor_collection.items():
                if key == "ALL":
                    continue

                sl_data = sensor.get_flat_data().copy()
                sl_data = utils.remove_9s(sl_data)
                sl_data = sl_data - int(sensor.height)
                time = utils.datenum2(sensor.get_time_vector())
                data_obj = [time, sl_data]

                file_name = month.get_mat_filename()[key]
                variable  = file_name.split('.')[0]

                save_folder = month.get_save_folder()  # t + station_id
                save_path = utils.get_top_level_directory(parent_dir=path, is_test_mode=is_test_mode) \
                            / utils.HIGH_FREQUENCY_FOLDER / save_folder / str(month.year)
                utils.create_directory_if_not_exists(save_path)

                matlab_obj = {'NNNN': variable, variable: np.transpose(data_obj, (1, 0))}
                try:
                    sio.savemat(Path(save_path / file_name), matlab_obj)
                    success.append({'title': "Success",
                                    'message': f"Success \n{file_name} Saved to {save_path}\n"})
                except IOError as e:
                    failure.append({'title': "Error",
                                    'message': ("Cannot Save to high frequency (.mat) data to"
                                                f"{save_path}\n{e}\n Please select a different path to save to")})

        if callback:
            callback(success, failure)

        return success, failure

    # MJW attempt on 4/9/2025 to fix filtering bug (beginning/ending data problem).
    def save_fast_delivery(self, din_path: str, path: str, is_test_mode: bool = False, merge: bool = True,
                           target_start_yyyymm: int = None, target_end_yyyymm: int = None,
                           callback: Callable = None):
        """
        Produce and save merged hourly and daily fast-delivery products.

        This builds a cross-month, merged hourly product (optionally filling
        gaps from prioritized channels) and a daily residual filtered product,
        then writes both ``.mat`` and legacy ``.dat`` files constrained to the
        target month range.

        Args:
            din_path: Path containing channel priority (``.din``) info.
            path: Parent directory for output files.
            is_test_mode: If ``True``, write to a sandbox/test location.
            merge: If ``True``, merge channels according to priority; otherwise
                use per-channel series as-is.
            target_start_yyyymm: Inclusive start month as ``YYYYMM``.
            target_end_yyyymm: Inclusive end month as ``YYYYMM``.
            callback: Optional function ``callback(success, failure)``.

        Returns:
            Tuple ``(success, failure)``. If processing fails early, partial
            results may be returned.

        Raises:
            ValueError: If the month range is not fully specified.
        """

        if target_start_yyyymm is None or target_end_yyyymm is None:
            raise ValueError("Both target_start_yyyymm and target_end_yyyymm must be specified.")

        target_start_time, target_end_time = self.get_target_month_range(target_start_yyyymm, target_end_yyyymm)

        # Todo: Refactor this into at least two more functions, one for daily fast delivery and one for hourly,
        # each saving to both .mat and .dat. But this entire code here is hideous in general and needs to be refactored.
        import scipy.io as sio
        success = []
        failure = []
        is_hourly = self.month_collection[0]._hourly_data

        # Step 1: Aggregate across all months.
        all_data_obj = {}
        all_data_obj_primary = {}
        all_times = []
        all_sealevels = []
        din_sensors_global = None
        reliable_sensor_global = None

        for month in self.month_collection:
            _data = month.sensor_collection.sensors
            station_num = month.station_id
            try:
                primary_sensors = utils.get_channel_priority(din_path, station_num)
            except Exception as e:
                print(f'ERROR: Problem getting primary sensors for station {station_num} from {din_path} - skipping FD creation.')
                return
            din_sensors = [x for x in primary_sensors if x in _data]

            if not din_sensors:
                raise ValueError(f'ERROR: No din sensors with data found in primary sensors for station {station_num}')

            # Assume first matching sensor across all months is good enough to be the reliable primary
            if reliable_sensor_global is None:
                reliable_sensor_global = din_sensors[0]
                din_sensors_global = din_sensors  # Save for later use

            for sens in din_sensors:
                key = sens.lower()
                if key not in all_data_obj:
                    all_data_obj[key] = {'time': [],
                                         'sealevel': [],
                                         'station': station_num
                                        }

                values = _data[sens].get_flat_data().copy()
                values = utils.remove_9s(values)
                values = values - int(_data[sens].height)
                all_data_obj[key]['time'].extend(utils.datenum2(_data[sens].get_time_vector()))
                all_data_obj[key]['sealevel'].extend(values)

        # Step 2: Convert to np arrays.
        for key in all_data_obj:
            all_data_obj[key]['time'] = np.array(all_data_obj[key]['time'])
            all_data_obj[key]['sealevel'] = np.array(all_data_obj[key]['sealevel'])

        # Step 3: Filter once for hourly/daily.
        ch_params = [{ch.lower(): 0} for ch in din_sensors_global]

        datenums = all_data_obj[reliable_sensor_global.lower()]['time']
        start_dt = self.datenum_to_datetime(datenums[0])
        end_dt = self.datenum_to_datetime(datenums[-1])

        try:
            if is_hourly:
                if merge:
                    hourly_merged_all = filt.channel_merge(all_data_obj, ch_params)
                else:
                    hourly_merged_all = all_data_obj
            else:
                data_hr_all = filt.hr_process(all_data_obj, start_dt, end_dt)
                if merge:
                    hourly_merged_all = filt.channel_merge(data_hr_all, ch_params)
                else:
                    hourly_merged_all = data_hr_all
        except Exception as e:
            print(f'ERROR: Issue producing hourly_merged_all - skipping fast delivery production.')
            return success, failure

        try:
            data_day_all = filt.day_119filt(hourly_merged_all, self.location[0])
        except Exception as e:
            print(f'ERROR: Issue producing daily data from hourly_merged_all (likely all NA data) - skipping fast delivery production.')
            return success, failure

        for month in self.month_collection:
            month_start = datetime(month.year, month.month, 1)
            if not (target_start_time <= month_start < target_end_time):
                continue  # Skip months outside the target range

            data_obj = {}  # holding data for all the sensors specified in the din file
            data_obj_primary = {}  # holding data only for the primary sensor
            sl_data = {}
            _data = month.sensor_collection.sensors
            station_num = month.station_id
            primary_sensors = utils.get_channel_priority(din_path, station_num)  # returns primary channel

            # Match primary sensor from the din file to the sensor in the data file because
            # sometimes the station might not have the sensor specified in the din file.
            din_sensors = [x for x in primary_sensors if x in month.sensor_collection.sensors]
            no_primary_data = False
            if not din_sensors:
                no_primary_data = True
                failure.append({'title': "Error", 'message': "Primary sensors listed in din file are {} but station {} "
                                                             "contains no data for any of the listed sensors. Hourly "
                                                             "and daily data will not be saved because saving hourly "
                                                             "data requires at least one primary sensor data to be "
                                                             "present even if the data is all 9999"
                               .format(', '.join(primary_sensors), station_num)})
                if callback:
                    callback(success, failure)
                return success, failure

            for reliable_sensor in din_sensors:
                sl_data[reliable_sensor] = _data[reliable_sensor].get_flat_data().copy()
                sl_data[reliable_sensor] = utils.remove_9s(sl_data[reliable_sensor])
                if np.isnan(sl_data[reliable_sensor]).all():
                    # jump to the next sensor if all data is nan
                    # if this is true for all iterations of the loop, then the daily and hourly data will be all 9999
                    no_primary_data = True
                    continue
                else:
                    # break out of the loop once we find a primary sensor with the data and that sensor will be the
                    # primary sensor
                    no_primary_data = False
                    break

            if no_primary_data:
                reliable_sensor = primary_sensors[0]
                if reliable_sensor in _data:
                    sl_data[reliable_sensor] = np.full(len(_data[reliable_sensor].get_flat_data().copy()), 9999)
                else:
                    failure.append({'title': "Error", 'message': f"Fallback primary sensor {reliable_sensor} not found in station {station_num} data."})
                    if callback:
                        callback(success, failure)
                    return success, failure
            else:
                sl_data[reliable_sensor] = sl_data[reliable_sensor] - int(_data[reliable_sensor].height)

            data_obj_primary[reliable_sensor.lower()] = {
                'time': utils.datenum2(_data[reliable_sensor].get_time_vector()),
                'station': station_num, 'sealevel': sl_data[reliable_sensor]
            }

            # Go through all the preferred sensors one more time that we can use their data to
            # generate hourly and daily data, where missing data from the primary sensor is filled
            # in with the secondary, and tertiary and so on.
            for sens in din_sensors:
                sl_data[sens] = _data[sens].get_flat_data().copy()
                sl_data[sens] = utils.remove_9s(sl_data[sens])
                sl_data[sens] = sl_data[sens] - int(_data[sens].height)
                data_obj[sens.lower()] = {
                    'time': utils.datenum2(_data[sens].get_time_vector()),
                    'station': station_num, 'sealevel': sl_data[sens]}

            # for channel parameters see filt.channel_merge function.
            ch_params = [{ch.lower(): 0} for ch in primary_sensors]
            year = _data[reliable_sensor].date.astype(object).year
            two_digit_year = str(year)[-2:]

            # Get time range for this month.
            start_time = datetime(month.year, month.month, 1)
            end_month = month.month + 1 if month.month < 12 else 1
            end_year = month.year if month.month < 12 else month.year + 1
            end_time = datetime(end_year, end_month, 1)

            # Mask data from global hourly/daily datasets using merged hourly data time.
            time_hr = hourly_merged_all['time']
            start_datenum = utils.datenum(start_time)
            end_datenum = utils.datenum(end_time)
            time_mask = (time_hr >= start_datenum) & (time_hr < end_datenum)

            # Extract the hourly slice (merged).
            data_hr = {
                'time': time_hr[time_mask],
                'station': month.station_id,
                'sealevel': hourly_merged_all['sealevel'][time_mask],
                'channel': hourly_merged_all['channel'][time_mask]
            }

            # Mask daily data using daily timestamps.
            time_day = data_day_all['time']
            day_mask = (time_day >= start_datenum) & (time_day < end_datenum)

            # Extract the daily slice (merged).
            data_day = {
                'time': time_day[day_mask],
                'station': month.station_id,
                'sealevel': data_day_all['sealevel'][day_mask],
                'channel': data_day_all['channel'][day_mask]
            }

            month_str = "{:02}".format(month.month)

            save_folder = month.get_save_folder()  # t + station_id
            save_path = utils.get_top_level_directory(parent_dir=path,
                                                      is_test_mode=is_test_mode) / utils.FAST_DELIVERY_FOLDER / save_folder \
                        / str(
                month.year)
            utils.create_directory_if_not_exists(save_path)

            hourly_filename = str(save_path) + '/' + 'th' + str(station_num) + two_digit_year + month_str
            daily_filename = str(save_path) + '/' + 'da' + str(station_num) + two_digit_year + month_str

            mean_val = np.nanmean(data_day['sealevel'])
            if np.isnan(mean_val):
                print(f"WARNING: Monthly mean is NaN for station {station_num}, month {month.month}, using 9999 as fallback.")
                monthly_mean = 9999
            else:
                monthly_mean = int(np.round(mean_val))

            hr_flat = data_hr['sealevel'].flatten() # Merged Sensors

            nan_ind_hr = np.argwhere(np.isnan(hr_flat))
            hr_flat[nan_ind_hr] = 9999
            sl_hr_round_up = np.round(hr_flat).astype(int)  # round up sealevel data and convert to int

            sl_hr_str = [str(x).rjust(5, ' ') for x in sl_hr_round_up]  # convert data to string

            # Format the date and name strings to match the legacy daily .dat format.
            month_str = str(month.month).rjust(2, ' ')
            station_name = month.station_id + self.name
            line_begin_str = '{}QC3 {}{}'.format(station_name.ljust(7), year, month_str)
            counter = 1

            try:
                sio.savemat(daily_filename + '.mat', data_day)
                # Remove nans, replace with 9999 to match the legacy files.
                nan_ind = np.argwhere(np.isnan(data_day['sealevel']))
                data_day['sealevel'][nan_ind] = 9999
                sl_round_up = np.round(data_day['sealevel']).astype(int)  # round up sealevel data and convert to int
                # right justify with 5 spaces
                sl_str = [str(x).rjust(5, ' ') for x in sl_round_up]  # convert data to string
                with open(daily_filename + '.dat', 'w') as the_file:
                    for i, sl in enumerate(sl_str):
                        if i % 11 == 0:
                            line_str = line_begin_str + str(counter) + " " + ''.join(sl_str[i:i + 11])
                            if counter == 3:
                                line_str = line_str.ljust(75)
                                final_str = line_str[:-(len(str(monthly_mean)) + 1)] + str(monthly_mean)
                                line_str = final_str
                            the_file.write(line_str + "\n")
                            counter += 1
                success.append({'title': "Success",
                                'message': "Success \n Daily Data Saved to " + str(save_path) + "\n"})
            except IOError as e:
                failure.append({'title': "Error",
                                'message': "Cannot Save Daily Data to " + daily_filename + "\n" + str(
                                    e) + "\n Please select a different path to save to"})

            # Get the location string from the header.
            location_str = month.sensor_collection.sensors[reliable_sensor].header[14:41]
            metadata_header = '{}{}FDH{}  {} TMZONE=GMT    REF=00000 60 {} {} M {}'. \
                format(month.station_id,
                       self.name[0:3],
                       reliable_sensor,
                       location_str,
                       month.name.upper(),
                       two_digit_year,
                       str(month.day_count))
            line_begin = '{}{} {} {}{}'.format(month.station_id,
                                               self.name[0:3],
                                               'QC3',
                                               str(year),
                                               str(month.month).rjust(2))

            day = 1
            counter = 0

            # Save hourly.
            try:
                sio.savemat(hourly_filename + '.mat', data_hr)
                with open(hourly_filename + '.dat', 'w') as the_file:
                    the_file.write(metadata_header + "\n")
                    for i, sl in enumerate(sl_hr_str):
                        if i != 0 and i % 24 == 0:
                            counter = 0
                            day += 1
                        if i % 12 == 0:
                            counter += 1
                            line_str = line_begin + str(day).rjust(2) + str(counter) + ''.join(
                                sl_hr_str[i:i + 12]).rjust(5)
                            the_file.write(line_str + "\n")
                    the_file.write('9' * 80 + "\n")
                success.append({'title': "Success",
                                'message': "Success \n Hourly Data Saved to " + str(save_path) + "\n"})
            except IOError as e:
                failure.append({'title': "Error",
                                'message': "Cannot Save Hourly Data to " + hourly_filename + "\n" + str(
                                    e) + "\n Please select a different path to save to"})

        if callback:
            callback(success, failure)

        return success, failure


    def save_to_annual_file(self, path: str, is_test_mode=False, callback: Callable = None):
        """ 
        Saves annual high frequency data to a .mat file. One annual file per sensor.

        The logic is as follows:

        1. Get all HF .mat files that exist for the given year and group them by sensor name.
        2. Find all the sensor/month combos that do not exist for the given year.
           Above step is necessary because it could happen that sometimes we remove a sensor from a station
           and sometimes we add it. This way, we won't miss out on any data.
        3. For each sensor/month combo that does not exist, create a new .mat file with adding a nan value for
           sea level in the middle of the month (15th of the month more precisely, arbitrarily chosen).
        4. Then again read in all the .mat files (now including the ones with NaN values) and combine them into one
           .mat file per sensor and save it to the annual folder.
        5. Delete the monthly .mat files that were created in step 3 (to clear up an confusion when an analyst
           looks at the monthly folder and sees a bunch of files with NaN values).

        TODO:

        6. Ensure we cannot do this if have station data loaded for two different years (i.e. month 12 and 1 loaded)
           OR disable the ability to load two different years of data at the same time. UPDATE 10/6/2022: For now
           we disabled the ability to load two different years of data at the same time. See below to do on how to
           incorporate multi year logic. UPDATE 11/13/2022: We now allow multi year loading. Still need to write
           tests for this.
        """

        import scipy.io as sio

        for year in self.year_range:
            year_str = str(year)
            month = self.month_collection[0]
            save_folder = month.get_save_folder()  # t + station_id
            mat_files_path = utils.get_top_level_directory(parent_dir=path,
                                                           is_test_mode=is_test_mode) / utils.HIGH_FREQUENCY_FOLDER / \
                             save_folder / str(
                year_str)

            # Get all the sensor .mat files and a list of months for each sensor.
            sensor_months = utils.get_hf_mat_files(mat_files_path)
            # convert to int to simplify the way we check if any months are missing
            for sensor, str_month in sensor_months.items():
                sensor_months[sensor] = [int(x) for x in str_month]

            annual_mat_files_path = utils.get_top_level_directory(parent_dir=path,
                                                                  is_test_mode=is_test_mode) / \
                                    utils.HIGH_FREQUENCY_FOLDER / save_folder

            # Figure out if a sensor was added or removed in a month by detecting a month that does not have a sensor 
            # that is present in the union of all sensors (months_sensor).
            # Save a .mat file for that sensor and month with a single NaN value.
            success = []
            failure = []
            missing = {}

            for sensor, month_list in sensor_months.items():
                missing[sensor] = get_missing_months(month_list)

            # Give the missing sensor for the given month only one NaN value for that month and save to .mat file.
            files_created = []
            for sensor, mon in missing.items():
                if missing[sensor]:
                    for m in mon:
                        # Give it two NaN values for that month (two needed because of the transpose).
                        time = [datenum(datetime(year, m, 15))]
                        sealevel = [np.nan]
                        data_obj = [time, sealevel]
                        variable = save_folder + year_str + '{:02d}'.format(m) + sensor

                        matlab_obj = {'NNNN': variable, variable: np.transpose(data_obj, (1, 0))}
                        variable = Path(variable + '.mat')
                        try:
                            sio.savemat(Path(mat_files_path / variable), matlab_obj)
                            files_created.append(Path(mat_files_path / variable))
                        except IOError as e:
                            failure.append({'title': "Error",
                                            'message': "ERROR {}. Cannot save temporary {} files ".format(e,
                                                                                                          str(variable))})

            # Get all the .mat files, including the ones we just created with NaN values.
            months_sensor = utils.get_hf_mat_files(mat_files_path, full_name=True)

            # Combine all year's HF .mat data to a single .mat file for each sensor.
            all_data = {}
            for sensor, file_name_list in months_sensor.items():
                for file in file_name_list:
                    filename = os.path.basename(file).split('/')[-1].split('.mat')[0]
                    data = sio.loadmat(file)
                    time = data[filename][:, 0]
                    sealevel = data[filename][:, 1]
                    # create an object with time and sealevel arrays for each sensor if this sensor is yet added to all
                    # data object, else append the data to the existing object
                    if sensor not in all_data:
                        all_data[sensor] = {'time': [time], 'sealevel': [sealevel]}
                    else:
                        all_data[sensor]['sealevel'] = np.append(all_data[sensor]['sealevel'], sealevel)
                        all_data[sensor]['time'] = np.append(all_data[sensor]['time'], time)

                data_obj = [all_data[sensor]['time'], all_data[sensor]['sealevel']]
                variable = save_folder + year_str + sensor

                matlab_obj = {'NNNN': variable, variable: np.transpose(data_obj, (1, 0))}
                variable = Path(variable + '.mat')

                try:
                    sio.savemat(Path(annual_mat_files_path / variable), matlab_obj)
                except IOError as e:
                    failure.append({'title': "Error",
                                    'message': "Error {}. Cannot Save Annual Data {} to {}".format(str(e),
                                                                                                   str(variable),
                                                                                                   str(annual_mat_files_path))})

            success.append({'title': "Success",
                            'message': "Success \n Annual .mat Data Saved to " + str(annual_mat_files_path) + "\n"})

            for file_name in files_created:
                try:
                    os.remove(file_name)
                except OSError as e:
                    failure.append({'title': "Error",
                                    'message': "Error {}. Cannot delete temporary {} files ".format(e, str(file_name))})

        if callback:
            callback(success, failure)

        return success, failure


class DataCollection:
    """
    Convenience wrapper for a station's combined multi-month arrays.

    Attributes:
        station: The :class:`Station` this collection represents.
        sensors: Combined arrays returned by :meth:`Station.combine_months`.
    """

    def __init__(self, station: Station = None):
        """
        Initialize a :class:`DataCollection`.

        Args:
            station: Station to wrap; if ``None``, attributes remain unset.
        """

        self.station = station
        self.sensors = self.combined_months()
