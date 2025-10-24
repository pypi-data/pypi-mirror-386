import os
import re
import copy
import calendar

import pandas as pd
import numpy as np

from typing import Optional
from collections import OrderedDict
from datetime import date, datetime
from uhslc_station_tools.sensor import SensorCollection, Sensor, Month, Station


def extract_rate(header: str) -> str:
    """
    Extract the sampling rate (minutes) from a header line.
    The function searches the header for all digit groups and returns the
    third-from-last group, which corresponds to the rate in the monp format.

    Args:
        header: A single header line from a monp data file.

    Returns:
        The sampling rate as a string (e.g., ``"60"`` or ``"15"``).
    """

    rate = re.findall(r'\d+', header)

    return rate[-3]

def resolve_century(two_digit_year: int) -> int:
    """
    Convert a 2-digit year int to 4-digit year int using 
    a simple pivot rule:
    - if yy <= current year (e.g., 25), return 2000 + yy
    - else return 1900 + yy

    Args:
        two_digit_year: A two digit year integer.

    Returns:
        The derived four digit year.
    """

    current_yy = date.today().year % 100
    yy = int(two_digit_year)

    if yy <= current_yy:
        return 2000 + yy
    else:
        return 1900 + yy

def determine_year(two_digit_str: str) -> int:
    """
    Convert a 2-digit year string to 4-digit year int using
    a simple pivot rule:
    - if yy <= current year (e.g., 25), return 2000 + yy
    - else return 1900 + yy

    Args:
        two_digit_year: A two digit year integer.

    Returns:
        The derived four digit year.
    """

    yy = int(two_digit_str)

    return resolve_century(yy)


class DataExtractor(Month):
    """
    Parse a single monp ``.dat`` file into sensor structures.

    The class opens and parses a monp-format monthly data file, extracting
    station metadata, sensor headers, time/value matrices, and unit handling. It
    also instantiates a :class:`SensorCollection` suitable for downstream use.

    Attributes:
        in_file: Open file handle for the input path (closed after parsing).
        headers: List of header lines (one per channel/sensor).
        frequencies: List of sampling rates for each sensor, as strings.
        refs: List of reference heights (``REF=``) extracted from headers.
        sensor_ids: List of station+type identifiers (e.g., ``"123Axx"``).
        init_dates: List of numpy ``datetime64`` initial dates per sensor.
        data_all: Mapping of sensor type (e.g., ``"PRS"``) to 2D numpy arrays.
        infos_time_col: Mapping of sensor type to corresponding time-info lines.
        prev_date: Unused legacy attribute (reserved).
        units: List of unit system used per sensor (``"Imperial"``/``"Metric"``).
        loc: ``[lat, lon]`` decimal-degree location extracted from headers.
        string_location: Raw location string slice from the header.
        sensors: :class:`SensorCollection` aggregated for the file.
        _hourly_data: True if file contains 60-minute headers (affects parsing).
        month_int: Month number parsed from filename (1-12).
        year: 4-digit year resolved from filenames.

    """

    def __init__(self, filename):
        """
        Initialize and fully parse the provided monp file.

        Args:
            filename: Path to a monp monthly data file (e.g., ``"t1091803.dat"``
                      or ``"sgana1801.dat"``).
        """

        self.in_file = open(filename, 'r')  # t1091803.dat, sgana1801.dat
        self.headers = []
        self.frequencies = []
        self.refs = []
        self.sensor_ids = []
        self.init_dates = []
        self.data_all = {}
        self.infos_time_col = {}
        self.prev_date = 0
        self.units = []
        self.loc = [0, 0]
        self.string_location = None

        self.sensors = SensorCollection()
        self._hourly_data = False

        # Parse file first to populate headers/init_dates/etc.
        self.parse_file(filename)

        # Parse filename to get dates - expect ...YYMM.dat filename format.
        base = os.path.basename(filename)
        self.month_int = int(base.split('.dat')[0][-2:])
        data_yy = base.split('.dat')[0][-4:-2]

        # Resolve the 4-digit year from the 2-digit year.
        self.year = determine_year(data_yy)

        # Some code elsewhere expects Month(...) already constructed.
        # Guard against empty headers when slicing [0][:3].
        station_code = (self.headers[0][:3] if self.headers and len(self.headers[0]) >= 3 else None)
        Month.__init__(self, self.month_int, self.year, self.sensors, station_code)

    def is_header(self, arg):
        """
        Return True if a line is a header line.

        The heuristic is the presence of the substring ``"LONG"`` in the line,
        which is expected in all station headers.

        Args:
            arg: A single line from the file.

        Returns:
            True if the line is considered a header; otherwise False.
        """

        return bool('LONG' in arg)

    def split_by_n(self, n, num):
        """
        Split a string into fixed-width chunks.

        Args:
            n: Chunk width.
            num: The input string to split.

        Returns:
            List of string chunks of width ``n`` (last chunk may be shorter).
        """

        return [num[i:i + n] for i in range(0, len(num), n)]

    def missing_dates(self, L):
        """
        Compute missing integers in a (mostly) consecutive integer list.

        Intended for day-of-month lists with sentinel boundaries.

        Args:
            L: Sorted list of integers where the first and last represent the
            lower/upper bounds used to detect gaps.

        Returns:
            Sorted list of integers within ``[L[0], L[-1]]`` that are missing
            from ``L``.
        """

        start, end = L[0], L[-1]

        return sorted(set(range(start, end + 1)).difference(L))

    def extract_lat(self, header):
        """
        Extract latitude (decimal degrees) from a header line.

        Args:
            header: Header line containing N/S hemisphere and DDM components.

        Returns:
            Signed latitude in decimal degrees (South negative).
        """

        # Extract a character to see if it is North or South.
        NorS = header[25]
        lat_deg = header[18:20]
        lat_min = header[21:23]
        lat_dec_deg = int(lat_deg) + int(lat_min) / 60

        return -lat_dec_deg if NorS == "S" else lat_dec_deg

    def extract_long(self, header):
        """
        Extract longitude (decimal degrees) from a header line.

        Args:
            header: Header line containing W/E hemisphere and DDM components.

        Returns:
            Signed longitude in decimal degrees (West negative).
        """

        WorE = header[40]  # West or East (W or E)
        long_deg = header[32:35]
        long_min = header[36:38]
        long_dec_deg = int(long_deg) + int(long_min) / 60

        return -long_dec_deg if WorE == "W" else long_dec_deg

    def extract_string_location(self, header):
        """
        Return the raw location slice from a header line.

        Args:
            header: Header line.

        Returns:
            Substring slice containing the free-form location text.
        """

        return header[14:41]

    def parse_file(self, filename):
        """
        Parse the input file, building sensors and internal structures.

        This method populates instance attributes such as ``headers``,
        ``frequencies``, ``refs``, ``sensor_ids``, ``init_dates``, ``data_all``,
        and the ``sensors`` collection. It also normalizes malformed values and
        fills missing-day gaps with sentinel values (``9999``) according to the
        expected sampling cadence.

        Args:
            filename: Path to the monp data file to parse.

        Side Effects:
            Reads from the file handle, appends to instance lists/mappings,
            and closes ``self.in_file`` at the end of parsing.
        """

        list_of_lists = []
        a_list = []
        counter = 0

        for line in self.in_file:
            a_list.append(line)
            if line.startswith('99999'):  # should probably use 80*"9"
                # print "Channel End, append a new channel"
                a_list.remove(a_list[-1])
                list_of_lists.append((counter, list(a_list)))
                a_list = []
                counter += 1

            if self.is_header(line):
                self.headers.append(line)
                rate = extract_rate(line)
                self.frequencies.append(rate)
                if rate == '60':
                    self._hourly_data = True
                self.refs.append(re.search('REF=([^ ]+) .*', line).group(1))

        for header in self.headers:
            # Safeguarding against the case a station number ever becomes a 4 digit.
            # Search for digits in the first element of the header and put the together.
            station_num = ''.join(map(str, [int(s) for s in header.split()[0][0:4] if s.isdigit()]))
            self.sensor_ids.append(station_num + header[6:9])

        self.loc = [self.extract_lat(self.headers[0]), self.extract_long(self.headers[0])]
        self.string_location = self.extract_string_location(self.headers[0])

        # Because file ends with two lines of 9s there is an empty list that needs to be deleted.
        if not self._hourly_data:
            del list_of_lists[-1]

        for sensor in range(len(self.sensor_ids)):

            data = []  # only sea level measurements (no time)
            info_time_col = []
            sensor_type = self.sensor_ids[sensor][-3:]

            if int(self.frequencies[sensor]) >= 5:
                lines_per_day = int(1440 / 12 / int((self.frequencies[sensor])))
            else:
                lines_per_day = int(1440 / 15 / int((self.frequencies[sensor])))

            try:
                pre_text = list_of_lists[sensor][1][1:][0][0:15]
            except Exception as e:
                print(f'ERROR: Issue processing {sensor_type} sensor in {filename} - skipping.')
                continue

            # 1) Figure out the missing date.
            try:
                m_length = int(list_of_lists[sensor][1][0:][0][77:79])
            except Exception as e:
                print(f'ERROR: Review header information for correct formatting for {sensor_type} sensor in {filename} - skipping.')
                continue

            if not self._hourly_data:
                # Need to initiate with 0 because we need to check if the first day in a month is missing.
                month_ar = [0]

                # Go through every line of data.
                for l in range(len(list_of_lists[sensor][1][1:])):
                    # find first row of each month to get all dates in the file
                    if l % lines_per_day == 0:
                        month_ar.append(int(list_of_lists[sensor][1][1:][l][15:17]))

                # Add upper month range + 1 to check if there are any consecutive days
                # including the last date missing.
                if month_ar[-1] != m_length:
                    month_ar.append(m_length + 1)

                # Check for missing date and reset the comparison array to default [0].
                missed_dates_ar = self.missing_dates(month_ar)
                if missed_dates_ar:
                    print("Missing dates", missed_dates_ar)

            # Copy the list with all the data so that we can modify it.
            lines_copy = list_of_lists[sensor][1][1:]
            if not self._hourly_data:

                # There might be multiple days missing so need to loop through all of them.
                for day in missed_dates_ar:
                    missing_date = day
                    missing_date_str = '{:>2}'.format(str(missing_date))

                    # Create and format an array of lines with dates and missing data.
                    bad_data_ar = []

                    # 2) Add lines_per_day lines with 9999 values and increase the line counter.
                    for l in range(lines_per_day):
                        if int(self.frequencies[sensor]) >= 5:
                            bad_data_ar.append(
                                pre_text + str(missing_date_str) + " " + '{:>2}'.format(str(l)) + " 9999" * 12 + "\n")
                        else:
                            bad_data_ar.append(
                                pre_text + str(missing_date_str) + " " + '{:>2}'.format(str(l)) + "9999" * 15 + "\n")

                    # Insert the missing date with missing data.
                    for b in range(len(bad_data_ar)):
                        lines_copy.insert((missing_date - 1) * lines_per_day + b, bad_data_ar[b])

            if self._hourly_data:
                init_date_lst = lines_copy[0][11:19].split()
            else:
                init_date_lst = lines_copy[0][8:17].split()

            init_date = None
            try:
                if len(init_date_lst) == 1 and len(init_date_lst[0]) == 8 and init_date_lst[0].isdigit():
                    date_str = init_date_lst[0]
                    year = date_str[:4]
                    month = date_str[4:6]
                    day = date_str[6:]
                elif len(init_date_lst) > 2:
                    year = init_date_lst[0]
                    month = init_date_lst[1]
                    day = init_date_lst[2]
                else:
                    month = init_date_lst[0][-2:]
                    year = init_date_lst[0][:-2]
                    day = init_date_lst[1]
                    init_date_lst[1] = init_date_lst[0][4:]

                if len(day) == 1:
                    day = "0" + day
                if len(month) == 1:
                    month = "0" + month

                if len(year) == 2:
                    year = str(determine_year(year))
                if len(year) == 1:
                    year = "200" + year

                init_date = np.datetime64("-".join([year, month, day]) + 'T00:00:00.000000')

            except Exception as e:
                print(f"ERROR: Review date information for {sensor_type} in {filename}: {e!r}")

                base = os.path.basename(filename).lower()

                if base.endswith(".dat"):
                    yymm = base.split(".dat")[0][-4:]
                    yy, mm = yymm[:2], yymm[2:]
                    yyyy = determine_year(yy)
                    init_date = np.datetime64(f"{int(yyyy):04d}-{int(mm):02d}-01T00:00:00.000000")

                # Case 2: Tide mat like t0222024prs.mat (4-digit year in name).
                elif base.endswith(".mat"):
                    m = re.search(r"(18|19|20)\d{2}", base)
                    if m:
                        yyyy = int(m.group(0))
                        # Month is not encoded in this name; default to first of January
                        init_date = np.datetime64(f"{yyyy:04d}-01-01T00:00:00.000000")

            # If we still couldn't determine a date, mark clearly and continue.
            if init_date is None:
                print(f"ERROR: Could not parse init date for {sensor_type} in {filename}; defaulting to 2000-01-01")
                init_date = np.datetime64("2000-01-01T00:00:00.000000")

            self.init_dates.append(init_date)

            for line in lines_copy:
                # Read each row of data into a list of floats and also save the non-sensor 
                # data part (0:21) for the output file.
                info_time_col.append(line[:20])
                if int(self.frequencies[sensor]) >= 5:
                    fields = self.split_by_n(5, line[20:].rstrip())  # for 5 digit data format
                else:
                    fields = self.split_by_n(4, line[20:].rstrip())  # for 4 digit data format
                for i, s in enumerate(fields):
                    if s in ('****', ' ****', '*****'):
                        print(f"LOG: Replacing known bad value: '{s}'")
                        fields[i] = '9999'
                    else:
                        try:
                            float(s)
                        except ValueError:
                            print(f"WARNING: Replacing malformed value: '{s}'")
                            fields[i] = '9999'

                row_data = [float(x) for x in fields]

                # And add this row to the entire data set.
                data.append(row_data)

            # Data prior to Spet 2015 was stored in Imperial units.
            if init_date < np.datetime64('2015-09-01'):
                self.units.append('Imperial')
            else:
                self.units.append('Metric')

            # Finally, convert the "list of lists" into a 2D array.
            self.infos_time_col[self.sensor_ids[sensor][-3:]] = info_time_col
            self.data_all[self.sensor_ids[sensor][-3:]] = np.array(data)
            frequency = self.frequencies[sensor]
            ref_height = self.refs[sensor]
            header = self.headers[sensor]

            try:
                _sensor = Sensor(rate=frequency, height=int(ref_height), sensor_type=sensor_type,
                                 date=self.init_dates[sensor],
                                 data=np.array(data), time_info=info_time_col, header=header)
            except Exception as e:
                print(f'ERROR: Issue processing {sensor_type} sensor in {filename} - skipping.')
                continue
            self.sensors.add_sensor(_sensor)

        self.in_file.close()


def update_station_month_collection(station, dat_file_path, dat_file_dates, station_id):
    """
    Insert PRD (tide prediction) sensors into each month and return aggregate.

    For each month in ``station.month_collection``, this function loads the
    corresponding ``*_tide_prediction.meta`` and ``*_tide_prediction.csv`` files,
    creates a PRD sensor by copying an existing sensor's structure, and fills it
    with resampled (15-minute) tide prediction values. It also moves PRD to the
    front of the sensors dict for predictable ordering.

    Args:
        station: Station object whose months will be augmented.
        dat_file_path: Directory path containing the meta and CSV prediction files.
        dat_file_dates: Iterable of date strings (``YYYYMM``) associated with the
                        loaded ``.dat`` files.
        station_id: Station identifier used in prediction filenames.

    Returns:
        A DataFrame concatenating all months' resampled tide predictions with a
        ``time`` column suitable for updating aggregate structures.
    """

    # Initialize aggregate tide prediction df.
    agg_tide_prediction_df = pd.DataFrame()

    # Establish appropriate meta and data file names and information within.
    for i, time in enumerate(dat_file_dates):
        yyyymm = f"{station.month_collection[i].year:04d}{station.month_collection[i].month:02d}"
        tide_file_prefix = f"{station_id}_MEDIAN_{yyyymm}_tide_prediction"
        tide_meta_file_name = tide_file_prefix + '.meta'
        tide_meta_file = os.path.join(dat_file_path, tide_meta_file_name)

        with open(tide_meta_file, "r") as file:
            data_header = file.read()
            match = re.search(r"REF=(\d+)", data_header)
            if match:
                switch_level = match.group(1)
            else:
                switch_level = 0
            match = re.match(r'(\d+)', data_header)
            if match:
                uh_id = match.group(1)
            else:
                uh_id = None

        tide_prediction_file_name = tide_file_prefix + '.csv'
        tide_prediction_file = os.path.join(dat_file_path, tide_prediction_file_name)

        # Copy structure of the sensor class to PRD for consistency and ease of data replacement.
        sensor_copy = next(iter(station.month_collection[i].sensor_collection.sensors))
        class_copy = station.month_collection[i].sensor_collection.sensors[sensor_copy]
        prd_class = copy.copy(class_copy)
        prd_class.type = 'PRD'
        station.month_collection[i].sensor_collection.sensors['PRD'] = prd_class
        station.month_collection[i].sensor_collection.sensors['PRD'].rate = '15'
        station.month_collection[i].sensor_collection.sensors['PRD'].header = data_header + '\n'
        station.month_collection[i].sensor_collection.sensors['PRD'].height = switch_level

        # Insert new tide data where needed in the sensor class.
        new_tide_df = pd.read_csv(tide_prediction_file, usecols=['time', 'prediction'])
        new_tide_df['time'] = pd.to_datetime(new_tide_df['time'])
        new_tide_df.set_index('time', inplace=True)
        start_of_month = pd.to_datetime(yyyymm + "01", format="%Y%m%d")
        end_of_month = start_of_month + pd.offsets.MonthEnd(1)
        end_of_month = end_of_month.replace(hour=23, minute=59)
        new_index = pd.date_range(start_of_month, end_of_month, freq='min')
        new_tide_df = new_tide_df.reindex(new_index)
        resampled_tide_df = new_tide_df.resample('15min').mean()
        resampled_tide_df.reset_index(inplace=True)
        agg_tide_prediction_df = pd.concat([agg_tide_prediction_df, resampled_tide_df], ignore_index=True)
        resampled_tide_prediction = (resampled_tide_df['prediction'].values).flatten()
        num_data_points = len(resampled_tide_prediction)
        resampled_data_points = int(num_data_points / 12)
        resampled_tide_prediction_2d = resampled_tide_prediction.reshape(resampled_data_points, 12)
        station.month_collection[i].sensor_collection.sensors['PRD'].data = resampled_tide_prediction_2d
        init_date = start_of_month.strftime('%Y-%m-%dT%H:%M:%S.%f')
        init_date = np.datetime64(init_date)
        station.month_collection[i].sensor_collection.sensors['PRD'].date = init_date
        time_info_times = np.arange(start_of_month, start_of_month + np.timedelta64(resampled_data_points*3, 'h'),
                                    np.timedelta64(3, 'h'))
        time_info_fmt = [
            f"TP {uh_id}  "
            f"{date.astype('datetime64[M]').astype(str).replace('-', '')}  "
            f"{date.astype('datetime64[D]').item().day}  "
            f"{date.astype('datetime64[h]').item().hour}"
            for date in time_info_times
        ]
        station.month_collection[i].sensor_collection.sensors['PRD'].time_info = time_info_fmt
        station.month_collection[i].sensor_collection.sensors = {'PRD': station.month_collection[i].sensor_collection.sensors.pop('PRD'),
                                                                 **station.month_collection[i].sensor_collection.sensors}

    return agg_tide_prediction_df


def update_station_aggregate_months(station, agg_tide_prediction_df):
    """
    Update ``station.aggregate_months`` to include PRD time/value arrays.

    Args:
        station: Station object whose ``aggregate_months`` will be updated in-place.
        agg_tide_prediction_df: DataFrame from
            :func:`update_station_month_collection` containing the concatenated
            tide predictions across months, with a ``time`` column.

    Returns:
        None. ``station.aggregate_months`` is modified in-place.
    """

    # Update the station aggregate months to include the new tide prediction.
    agg_tide_prediction_flat = (agg_tide_prediction_df['prediction'].values).flatten()
    new_tide_entry = {'PRD': agg_tide_prediction_flat}
    station.aggregate_months['data'] = {**new_tide_entry, **station.aggregate_months['data']}
    agg_tide_prediction_df.rename(columns={'index': 'time'}, inplace=True)
    prd_time = agg_tide_prediction_df['time'].tolist()
    station.aggregate_months['time']['PRD'] = np.array(prd_time, dtype='datetime64[us]')
    prd_time_dict = {'PRD': station.aggregate_months['time'].pop('PRD')}
    ordered_time = OrderedDict(prd_time_dict)
    ordered_time.update(station.aggregate_months['time'])
    station.aggregate_months['time'] = dict(ordered_time)
    prd_outlier_dict = {'PRD': np.array([], dtype=np.int64)}
    station.aggregate_months['outliers'] = {**prd_outlier_dict, **station.aggregate_months['outliers']}


def load_station_data(file_names):
    """
    Load one or more monp files and return a fully populated Station.

    Each input file is parsed via :class:`DataExtractor`. A synthetic "ALL"
    sensor is added to each month to support GUI behavior. If PRD predictions do
    not exist and the file prefix indicates a station (``'s'``), tide prediction
    data are injected using the helper functions above.

    Args:
        file_names: Iterable of monp data file paths to load (same station).

    Returns:
        A :class:`Station` instance with data aggregated across the provided
        months and PRD predictions added when applicable.
    """

    # Create DataExtractor for each month that was loaded into program
    months = []
    for file_name in file_names:
        month = DataExtractor(file_name)
        # An empty sensor, used to create "ALL" radio button in the GUI
        all_sensor = Sensor(None, None, 'ALL', None, None, None, None)
        month.sensors.add_sensor(all_sensor)
        # month = Month(month=month_int, sensors=month.sensors)
        months.append(month)

    months.sort(key=lambda m: (m.year, m.month))

    # The reason months[0] is used is because the program only allows to load
    # multiple months for the same station, so the station sensors should be the same
    # But what if a sensor is ever added to a station??? Check with fee it this ever happens
    name = months[0].headers[0][3:6]
    location = months[0].loc

    station = Station(name=name, location=location, month=months)

    # Determine to use new tide prediction based on existence of PRD in sensors.
    file_prefix = os.path.basename(file_names[0])
    if 'PRD' not in station.month_collection[0].sensor_collection.sensors and file_prefix[0] == 's':

        # Extract needed metadata for tide prediction.
        dat_file_path = os.path.dirname(file_names[0])
        dat_file_names = [os.path.basename(path) for path in file_names]
        dat_file_dates = [re.search(r'\d+', filename).group() for filename in dat_file_names]
        station_id = dat_file_names[0][1:5]

        # Update the station month collection and aggregate months to include the new tide prediction.
        agg_tide_prediction_df = update_station_month_collection(station, dat_file_path, dat_file_dates, station_id)
        update_station_aggregate_months(station, agg_tide_prediction_df)

    return station
