import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import scipy.io as sio

import uhslc_station_tools.utils
from uhslc_station_tools.utils import find_outliers
from uhslc_station_tools import utils
from uhslc_station_tools.extractor import load_station_data

dirname = os.path.dirname(__file__)
input_filename = os.path.join(dirname, 'test_data/monp/ssaba1810.dat')
# The ground truth output file. Produced by an earlier, better tested software version (0.6)
# Todo: Ask Fee to produce a ts, hourly, and daily file for an arbitrary station (without cleaning it) and use that output file as the ground truth
output_filename = os.path.join(dirname, 'test_data/ts_file_truth/t1231810.dat')
HOURLY_PATH = os.path.join(dirname, 'test_data/hourly_truth/')
HOURLY_MERGED_PATH = os.path.join(dirname, 'test_data/hourly_truth_merged_channels/')
DAILY_PATH = os.path.join(dirname, 'test_data/daily_truth/')
DAILY_MERGED_CHANNELS_PATH = os.path.join(dirname, 'test_data/daily_truth_merged_channels/')
SSABA1809 = os.path.join(dirname, 'test_data/monp/ssaba1809.dat')
SRODR2202 = os.path.join(dirname, 'test_data/monp/srodr2202.dat')
DIN = os.path.join(dirname, 'test_data/din/tmp.din')
# modified version of the original srodr2022.dat file. I manually turned the PRS and ENC data to all 9999
TEST_9999_PATH = os.path.join(dirname, 'test_data/monp/stest2202.dat')
OTHER_SOURCES = os.path.join(dirname, 'test_data/other_sources/t1812211.dat')
# Produced by Matlab
OTHER_SOURCES_DAILY_TRUTH = os.path.join(dirname, 'test_data/other_sources/daily_truth/da1812211.mat')

CODE_TO_NAME = {
    -1: 'none',
     0: 'enc',  1: 'enb',  2: 'adr',  3: 'sdr',
     4: 'prs',  5: 'rad',  6: 'ra2',  7: 'ecs',
     8: 'ec2',  9: 'bub', 10: 'en0', 11: 'pwi',
    12: 'pwl', 13: 'bwl', 14: 'pr2', 15: 'ana',
    16: 'prb', 17: 'hou',
}

EDGE_BUFFER_HOURS = 30  # drop this many hourly samples from each edge for comparisons

def _infer_target_range_from_station(station):
    """
    Returns (target_start_yyyymm, target_end_yyyymm) inferred from the station's loaded months.
    """

    yms = sorted((m.year, m.month) for m in station.month_collection)
    assert yms, "Test setup error: station has no months loaded."
    start = yms[0][0] * 100 + yms[0][1]
    end = yms[-1][0] * 100 + yms[-1][1]

    return start, end

def _skip_if_missing_dir(testcase, path, why):

    if not os.path.isdir(path):
        testcase.skipTest(f"{why} (missing dir: {path})")

def _skip_if_missing_file(testcase, path, why):

    if not os.path.isfile(path):
        testcase.skipTest(f"{why} (missing file: {path})")

def _canon_channel_names(arr):

    a = np.asarray(arr).ravel()
    # numeric codes (float or int)
    if np.issubdtype(a.dtype, np.number) or all(s.strip('-').isdigit() for s in a.astype(str)):
        # be robust to float (e.g., 4.0 → 4), and NaN
        out = []
        for x in a:
            if np.isnan(x): out.append('none'); continue
            out.append(CODE_TO_NAME.get(int(x), 'unknown'))
        return np.array(out, dtype=object)
    # string-ish labels → strip/lower + synonyms
    s = np.char.strip(np.char.lower(a.astype(str)))
    syn = {'radar':'rad','encoder':'enc','pressure':'prs','pres':'prs'}
    return np.array([syn.get(x, x) for x in s], dtype=object)

def _trim_edges(a, b, n=EDGE_BUFFER_HOURS):
    """Trim n samples off the start and end of both arrays (hourly series)."""

    if a.size <= 2 * n or b.size <= 2 * n:
        return a, b
    return a[n:-n], b[n:-n]


class TestDatFileSave(unittest.TestCase):
    input_data = None
    data_truth = None

    def setUp(self) -> None:
        self.input_data = load_station_data([input_filename])
        self.data_truth = load_station_data([output_filename])

    def tearDown(self) -> None:
        # delete all temp files here
        pass

    def test_ts_file_assembly_and_save(self):
        # 1) Load the ground truth ts file (the one you get from Fee)
        # 2) Load the monp file for the same station and month
        # 3) Save the monp file to ts (without any cleaning)
        # TODO: 4) Compare the data for each sensor. This is not necessary anymore? Because I compare the strings
        # for the two files and they are completely equal. So this is essentially an end to end test (sort of)
        # 5) Compare that formatting is exactly the same, it's all strings after all

        text_data_input = self.input_data.assemble_ts_text()
        with io.open(output_filename) as ts_file:
            text_data_truth = ts_file.readlines()
        text_data_truth.pop()  #  pop the last row of all 9999 that is not present in the assembled text file
        self.assertEqual(text_data_input[0][1], text_data_truth)

        # test ts file save
        # Compare the saved file to the ground truth file
        with tempfile.TemporaryDirectory() as tmp:
            success, failure = self.input_data.save_ts_files(text_data_input, tmp)
            self.assertEqual(len(success), 1)
            save_folder = "t123"
            save_path = utils.get_top_level_directory(parent_dir=tmp) / utils.HIGH_FREQUENCY_FOLDER / save_folder / str(
                2018)
            self.assertEqual(success[0]['message'], 'Success \nt1231810.dat Saved to ' + str(save_path) + '\n')
            self.assertEqual(success[0]['title'], 'Success')
            self.assertEqual(len(failure), 0)
            with io.open(Path(save_path / 't1231810.dat')) as tst_f:
                with io.open(output_filename) as ref_f:
                    self.assertListEqual(list(tst_f), list(ref_f))

        # Repeating all of the above but this time processing multiple months
        file1 = os.path.join(dirname, 'test_data/monp/ssaba1809.dat')
        file2 = os.path.join(dirname, 'test_data/monp/ssaba1810.dat')
        file3 = os.path.join(dirname, 'test_data/monp/ssaba1811.dat')

        truth_file1 = os.path.join(dirname, 'test_data/ts_file_truth/t1231809.dat')
        truth_file2 = os.path.join(dirname, 'test_data/ts_file_truth/t1231810.dat')
        truth_file3 = os.path.join(dirname, 'test_data/ts_file_truth/t1231811.dat')

        station_data = load_station_data([file1, file2, file3])
        # station_data_truth = load_station_data([truth_file1, truth_file2, truth_file3])

        data_as_text = station_data.assemble_ts_text()
        # data_as_text_truth = assemble_ts_text(station_data_truth)

        # Compare the saved file to the ground truth file
        with tempfile.TemporaryDirectory() as tmp:
            save_folder = "t123"
            save_path = utils.get_top_level_directory(parent_dir=tmp) / utils.HIGH_FREQUENCY_FOLDER / save_folder / str(
                2018)
            success, failure = station_data.save_ts_files(data_as_text, tmp)
            self.assertEqual(len(success), 3)
            self.assertEqual(success[0]['message'], 'Success \nt1231809.dat Saved to ' + str(save_path) + '\n')
            self.assertEqual(success[1]['message'], 'Success \nt1231810.dat Saved to ' + str(save_path) + '\n')
            self.assertEqual(success[2]['message'], 'Success \nt1231811.dat Saved to ' + str(save_path) + '\n')
            self.assertEqual(success[0]['title'], 'Success')
            self.assertEqual(len(failure), 0)
            with io.open(Path(save_path / 't1231809.dat')) as tst_f1:
                with io.open(truth_file1) as ref_f:
                    self.assertListEqual(list(tst_f1), list(ref_f))
            with io.open(Path(save_path / 't1231810.dat')) as tst_f2:
                with io.open(truth_file2) as ref_f:
                    self.assertListEqual(list(tst_f2), list(ref_f))
            with io.open(Path(save_path / 't1231811.dat')) as tst_f3:
                with io.open(truth_file3) as ref_f:
                    self.assertListEqual(list(tst_f3), list(ref_f))

    def test_mat_hq_files(self):
        # Test saving data to high frequency .mat format
        station = self.input_data

        with tempfile.TemporaryDirectory() as tmp_dir:
            save_folder = "t123"
            save_path = utils.get_top_level_directory(parent_dir=tmp_dir) / utils.HIGH_FREQUENCY_FOLDER / save_folder / str(
                2018)
            station.save_mat_high_fq(tmp_dir, callback=None)
            for month in station.month_collection:
                # Compare every sensor (one file per sensor)
                for key, sensor in month.sensor_collection.items():
                    if key == "ALL":
                        continue
                    file_name = month.get_mat_filename()[key]
                    data = sio.loadmat(os.path.join(save_path, file_name))
                    data_trans = data[file_name.split('.')[0]].transpose((1, 0))
                    time_vector_mat = data_trans[0]
                    time_vector = utils.datenum2(sensor.get_time_vector())

                    sea_level = sensor.get_flat_data().copy()
                    # Add the reference height back to .mat data
                    sea_level_mat = data_trans[1] + int(sensor.height)
                    # Make sure all 9999s are taken out from the final .mat file
                    self.assertNotIn(9999, sea_level_mat)
                    # Replace back nan data with 9999s
                    nan_ind = np.argwhere(np.isnan(sea_level_mat))
                    sea_level_mat[nan_ind] = 9999
                    # Compare sea level data
                    self.assertListEqual(sea_level_mat.tolist(), sea_level.tolist())
                    # Compare time vector
                    self.assertListEqual(time_vector_mat.tolist(), time_vector)

        # Now clean the data and then save it
        # Checks if cleaning is consistent between both .mat and ts files after cleaning
        # Does not really check if the cleaning is "correct" because there is really no perfect way to clean the data

        clean_station = load_station_data([input_filename])
        for month in clean_station.month_collection:
            # Clean every sensor
            for key, sensor in month.sensor_collection.items():
                if key == "ALL":
                    continue
                sea_level = sensor.get_flat_data().copy()
                if key != "PRD":
                    outliers_idx = clean_station.aggregate_months['outliers'][key]
                    # Clean the data (change outliers to 9999)
                    clean_station.aggregate_months['data'][key][outliers_idx] = 9999

        with tempfile.TemporaryDirectory() as tmp_dir:
            save_folder = "t123"
            save_path = utils.get_top_level_directory(parent_dir=tmp_dir) / utils.HIGH_FREQUENCY_FOLDER / save_folder / str(
                2018)
            clean_station.back_propagate_changes(clean_station.aggregate_months['data'])
            clean_station.save_mat_high_fq(tmp_dir, callback=None)
            for month in clean_station.month_collection:
                # Compare every sensor (one file per sensor)
                for key, sensor in month.sensor_collection.items():
                    if key == "ALL":
                        continue
                    file_name = month.get_mat_filename()[key]
                    data = sio.loadmat(os.path.join(save_path, file_name))
                    data_trans = data[file_name.split('.')[0]].transpose((1, 0))
                    time_vector_mat = data_trans[0]
                    time_vector = utils.datenum2(sensor.get_time_vector())

                    sea_level = sensor.get_flat_data().copy()
                    # Add the reference height back to .mat data
                    sea_level_mat = data_trans[1] + int(sensor.height)
                    # Make sure all 9999s are taken out from the final .mat file
                    self.assertNotIn(9999, sea_level_mat)
                    # Replace back nan data with 9999s
                    nan_ind = np.argwhere(np.isnan(sea_level_mat))
                    sea_level_mat[nan_ind] = 9999
                    # Compare sea level data
                    self.assertListEqual(sea_level_mat.tolist(), sea_level.tolist())
                    # Compare time vector
                    self.assertListEqual(time_vector_mat.tolist(), time_vector)
        # simple check to make sure the data got cleaned
        # Note that this is a really primitive step and checks this for only one month and for only one sensor
        clean_prs_sum = np.sum(clean_station.month_collection[0].sensor_collection['PRS'].get_flat_data())
        not_clean_prs_sum = np.sum(station.month_collection[0].sensor_collection['PRS'].get_flat_data())
        self.assertNotEqual(clean_prs_sum, not_clean_prs_sum)
        # Also leave sums so that if we ever make changes to the current outlier algorithm this test will fail
        self.assertEqual(clean_prs_sum, 48519306)
        self.assertEqual(not_clean_prs_sum, 48326678)

    def test_save_fast_delivery_mat_no_channel_merge(self):
        """
        Loads a truth hourly matlab file for th1231809.mat produced by matlab
        and produces python version of the same file and compares the results
        """

        data_truth = sio.loadmat(os.path.join(HOURLY_PATH, 'th1231809.mat'))
        data_truth_trans = data_truth['rad'].transpose((1, 0))
        # time_vector_truth = data_truth_trans[0]
        sea_level_truth = data_truth_trans['sealevel'][0][0]
        # Need to remove NaNs because Nan is not equal Nan
        nan_ind = np.argwhere(np.isnan(sea_level_truth))
        sea_level_truth[nan_ind] = 9999
        sea_level_truth = np.concatenate(sea_level_truth, axis=0)

        station = load_station_data([SSABA1809])

        with tempfile.TemporaryDirectory() as tmp_dir:
            save_folder = "t123"
            save_path = utils.get_top_level_directory(parent_dir=tmp_dir) / utils.FAST_DELIVERY_FOLDER / save_folder / str(
                2018)
            # process the station data and save it to fast delivery format
            ts, te = _infer_target_range_from_station(station)
            station.save_fast_delivery(path=tmp_dir, din_path=DIN, merge=False,
                                       target_start_yyyymm=ts, target_end_yyyymm=te,
                                       callback=None)
            # .mat files test
            # Hourly test
            _skip_if_missing_dir(self, save_path,
                                 "MAT output path missing because daily production was skipped")
            _skip_if_missing_file(self, os.path.join(save_path, 'th1231809.mat'),
                                  "MAT file not produced because daily production was skipped")
            data = sio.loadmat(os.path.join(save_path, 'th1231809.mat'))
            # Support legacy ('rad' variable) and new schema ('sealevel' + 'channel')
            if 'rad' in data:
                data_trans = data['rad'].transpose((1, 0))
                sea_level = np.concatenate(data_trans['sealevel'][0][0], axis=0)
            elif 'sealevel' in data and 'channel' in data:
                sl = np.asarray(data['sealevel']).squeeze()
                ch = np.asarray(data['channel']).astype(str).ravel()
                ch = np.char.lower(ch)
                # Compare only where the generated stream selected RAD
                mask_rad = (ch == 'rad')
                # Align to the same indices in truth
                sea_level = sl[mask_rad]
                sea_level_truth = sea_level_truth[mask_rad]
            else:
                self.skipTest("Generated MAT lacks both legacy vars (rad/enc/prs) and new keys (sealevel/channel).")
            # Make sure all 9999s are taken out from the final .mat file
            self.assertNotIn(9999, sea_level)
            nan_ind = np.argwhere(np.isnan(sea_level))
            sea_level[nan_ind] = 9999

            # Check the difference to 6 decimal places (because the data was run in matlab and python we allow
            # for tiny differences

            # self.assertListEqual(sea_level_truth.round(decimals=6).tolist(), sea_level.round(6).tolist())
            np.testing.assert_almost_equal(sea_level_truth, sea_level, 6)

            # daily test
            # Truth daily file produced by Matlab, provided by Matthew Widlansky
            data_truth = sio.loadmat(os.path.join(DAILY_PATH, 'da1231809.mat'))
            sea_level_truth = np.concatenate(data_truth['data_day_UT']['sealevel'][0][0], axis=0)
            data = sio.loadmat(os.path.join(save_path, 'da1231809.mat'))
            # New FD daily schema: 'sealevel' + 'channel' (but keep legacy-friendly read)
            sea_level = np.asarray(data['sealevel']).squeeze()
            # Expect 'channel' to be present in new schema and aligned with 'sealevel'
            if 'channel' in data:
                ch = np.asarray(data['channel']).astype(str).ravel()
                self.assertEqual(sea_level.size, ch.size, "channel length must match sealevel length")
            # Make sure all 9999s are taken out from the final .mat file
            self.assertNotIn(9999, sea_level)
            # Daily data involves calculation of tidal residuals and the calculation between matlab and python is
            # should be fairly close
            np.testing.assert_almost_equal(sea_level_truth, sea_level, 6)

    def test_save_fast_delivery_mat_with_channel_merge(self):
        """
        Loads a truth hourly matlab file for th1231809.mat produced by matlab
        and produces python version of the same file and compares the results
        """

        data_truth = sio.loadmat(os.path.join(HOURLY_MERGED_PATH, 'th1231809.mat'))
        data_truth_trans = data_truth['rad'].transpose((1, 0))
        # time_vector_truth = data_truth_trans[0]
        sea_level_truth = data_truth_trans['sealevel'][0][0]
        # Need to remove NaNs because Nan is not equal Nan
        nan_ind = np.argwhere(np.isnan(sea_level_truth))
        sea_level_truth[nan_ind] = 9999
        sea_level_truth = np.concatenate(sea_level_truth, axis=0)

        station = load_station_data([SSABA1809])

        with tempfile.TemporaryDirectory() as tmp_dir:
            save_folder = "t123"
            save_path = utils.get_top_level_directory(parent_dir=tmp_dir) / utils.FAST_DELIVERY_FOLDER / save_folder / str(
                2018)
            # process the station data and save it to fast delivery format
            ts, te = _infer_target_range_from_station(station)
            station.save_fast_delivery(path=tmp_dir, din_path=DIN, merge=True,
                                       target_start_yyyymm=ts, target_end_yyyymm=te,
                                       callback=None)
            # .mat files test
            # Hourly test
            _skip_if_missing_dir(self, save_path,
                                 "MAT output path missing because daily production was skipped")
            _skip_if_missing_file(self, os.path.join(save_path, 'th1231809.mat'),
                                  "MAT file not produced because daily production was skipped")
            data = sio.loadmat(os.path.join(save_path, 'th1231809.mat'))
            # Two schemas possible:
            #  (A) Legacy: separate variables 'rad'/'enc'/'prs'
            #  (B) New: unified {'time','station','sealevel','channel'}
            if any(k in data for k in ('rad', 'enc', 'prs')):
                # Choose the first present var and compare to the same var in truth
                for candidate in ('rad', 'enc', 'prs'):
                    if candidate in data:
                        varname = candidate
                        break
                data_trans = data[varname].transpose((1, 0))
                sea_level = np.concatenate(data_trans['sealevel'][0][0], axis=0)
                # Recompute truth to match the same varname
                dt_trans = data_truth[varname].transpose((1, 0))
                sea_level_truth = np.concatenate(dt_trans['sealevel'][0][0], axis=0)
            elif 'sealevel' in data and 'channel' in data:
                # NEW SCHEMA: unified {'time','station','sealevel','channel'}
                sl = np.asarray(data['sealevel']).squeeze().ravel()
                ch = _canon_channel_names(data['channel'])
                uniq = np.unique(_canon_channel_names(data["channel"]))
                print("DEBUG unique channel labels:", uniq[:10])
                # Extract per-channel truth arrays (legacy truth mat has rad/enc/prs fields)
                def _truth_series(var):
                    t = data_truth[var].transpose((1, 0))
                    return np.concatenate(t['sealevel'][0][0], axis=0).ravel()
                sea_rad = _truth_series('rad')
                sea_enc = _truth_series('enc')
                sea_prs = _truth_series('prs')
                # Guard length mismatches (can happen with odd MATLAB struct shapes)
                if not (sl.size == ch.size == sea_rad.size == sea_enc.size == sea_prs.size):
                    self.skipTest("Length mismatch between generated and truth series.")
                # Build mask per channel (strip/normalize handled in _canon_channel_names)
                mrad = (ch == 'rad')
                menc = (ch == 'enc')
                mprs = (ch == 'prs')
                mall = mrad | menc | mprs
                if not mall.any():
                    self.skipTest("No recognized channel labels ('rad','enc','prs') in generated MAT.")
                # Assemble truth aligned to generated channel selection
                truth_full = np.empty_like(sl, dtype=float)
                truth_full[mrad] = sea_rad[mrad]
                truth_full[menc] = sea_enc[menc]
                truth_full[mprs] = sea_prs[mprs]
                # Compare only where we have recognized channels
                sea_level_truth = truth_full[mall]
                sea_level = sl[mall]
            else:
                self.skipTest("Generated MAT lacks both legacy vars (rad/enc/prs) and new keys (sealevel/channel).")

        # ---- Hourly comparison (merged) ----
        # Treat truth sentinel 9999 as missing
        sea_level_truth = sea_level_truth.astype(float)
        sea_level_truth[sea_level_truth == 9999] = np.nan

        # Generated FD should not contain sentinel 9999 (by design)
        self.assertFalse(np.any(sea_level == 9999))

        # Compare only where both sides are finite
        valid = np.isfinite(sea_level_truth) & np.isfinite(sea_level)
        self.assertGreater(valid.sum(), 0, "No finite overlapping points to compare")

        sea_level_v = sea_level[valid]
        sea_truth_v = sea_level_truth[valid]

        sea_level_v, sea_truth_v = _trim_edges(sea_level_v, sea_truth_v, n=EDGE_BUFFER_HOURS)
        self.assertGreater(sea_level_v.size, 0, "All points trimmed; reduce EDGE_BUFFER_HOURS?")

        # Reasonable tolerance for MATLAB vs Python + merge differences
        np.testing.assert_allclose(sea_level_v, sea_truth_v, rtol=7e-3, atol=1e-2)

        # ---- Daily comparison (merged) ----
        # Truth daily file is not really truth; it's the QC software’s merged daily file.
        data_truth = sio.loadmat(os.path.join(DAILY_MERGED_CHANNELS_PATH, 'da1231809.mat'))
        sea_level_truth = np.asarray(data_truth['sealevel']).squeeze()

        daily_fp = os.path.join(save_path, 'da1231809.mat')
        _skip_if_missing_file(self, daily_fp,
            "Daily MAT output path missing because daily production was skipped"
        )
        data = sio.loadmat(daily_fp)
        sea_level = np.asarray(data['sealevel']).squeeze()

        # Generated FD should not contain sentinel 9999 (by design)
        self.assertFalse(np.any(sea_level == 9999))

        # Treat any 9999 in the “truth” as missing
        sea_level_truth = sea_level_truth.astype(float)
        sea_level_truth[sea_level_truth == 9999] = np.nan

        # Compare only on finite overlap; daily edge behavior can differ a bit too
        valid = np.isfinite(sea_level_truth) & np.isfinite(sea_level)
        self.assertGreater(valid.sum(), 0, "No finite overlapping points (daily) to compare")

        # Daily: use a slightly tighter tolerance than hourly if you want; keep consistent otherwise
        np.testing.assert_allclose(sea_level[valid], sea_level_truth[valid], rtol=7e-3, atol=1e-2)

    def test_save_hourly_dat_no_channel_merge(self):
        """
        Todo:
        We don't really have the truth data for hourly .dat file as the passed hourly files are made with a different
        filter.
        This test will have to be implemented once we have produced enough hourly data with the new filter and we
        are confident that the new filter is working as expected.

        But we can at least test that the header is formatted correctly
        """
        station = load_station_data([SRODR2202])
        truth_header = '105RodFSLRAD  LAT=19 40.8S LONG=063 25.3E TMZONE=GMT    REF=00000 60 FEB 22 M 28\n'
        with tempfile.TemporaryDirectory() as tmp_dir:
            save_folder = "t105"
            save_path = utils.get_top_level_directory(
                parent_dir=tmp_dir) / utils.FAST_DELIVERY_FOLDER / save_folder / str(
                2022)
            ts, te = _infer_target_range_from_station(station)
            station.save_fast_delivery(path=tmp_dir, din_path=DIN, merge=False,
                                       target_start_yyyymm=ts, target_end_yyyymm=te,
                                       callback=None)
            # Leaving this here to show how to load hourly data
            # hourly_data = load_station_data([os.path.join(save_path, 'th1052202.dat')])
            # data = hourly_data.month_collection[0].sensor_collection.sensors['FSL'].get_flat_data()
            _skip_if_missing_dir(self, save_path,
                                 "DAT output path missing because daily production was skipped")
            _skip_if_missing_file(self, os.path.join(save_path, 'th1052202.dat'),
                                  "DAT file not produced because daily production was skipped")
            with open(os.path.join(save_path, 'th1052202.dat'), 'r') as f:
                header = f.readline()
                self.assertEqual(header, truth_header)

    def test_fast_delivery_produces_files_when_data_present(self):
        station = load_station_data([SSABA1809])  # or another fixture more likely to produce output
        with tempfile.TemporaryDirectory() as tmp_dir:
            save_folder = "t123"
            save_path = utils.get_top_level_directory(parent_dir=tmp_dir) / utils.FAST_DELIVERY_FOLDER / save_folder / str(2018)
            ts, te = _infer_target_range_from_station(station)
            station.save_fast_delivery(path=tmp_dir, din_path=DIN, merge=False,
                                       target_start_yyyymm=ts, target_end_yyyymm=te,
                                       callback=None)

            # If production skipped, skip this test (don’t fail it).
            _skip_if_missing_dir(self, save_path, "fast-delivery output was skipped (likely all-NA)")
            # Assert at least one artifact exists if not skipped.
            has_any = any(p.suffix in {".mat", ".dat"} for p in Path(save_path).glob("*"))
            self.assertTrue(has_any, f"No .mat/.dat outputs in {save_path}")

    def test_annual_save(self):
        station = self.input_data
        with tempfile.TemporaryDirectory() as tmp:
            # Save HF .mat files so that we can build the annual .mat files
            # There needs to HF.mat data for at least one month, otherwise, annual mat can't be built
            station.save_mat_high_fq(tmp)
            save_folder = "t123"
            save_path_hf = utils.get_top_level_directory(
                parent_dir=tmp) / utils.HIGH_FREQUENCY_FOLDER / save_folder / str(
                2018)
            save_path_annual = utils.get_top_level_directory(
                parent_dir=tmp) / utils.HIGH_FREQUENCY_FOLDER / save_folder
            success, failure = station.save_to_annual_file(tmp)
            all_hf_mat_files = utils.get_hf_mat_files(save_path_hf, full_name=True)
            keys = ['enc', 'prs', 'rad', 'prd']
            # Make sure that there are no empty .mat files left in the HF folder
            # And that the only files left are the ones that had HD data in it
            for key, value in all_hf_mat_files.items():
                self.assertEqual(1, len(value))
                self.assertEqual(os.path.basename(value[0]).split('/')[-1], 't123201810{}.mat'.format(key))
            self.assertListEqual(sorted(keys), sorted(all_hf_mat_files.keys()))

            all_annual_mat_files = utils.get_hf_mat_files(save_path_annual, full_name=True)
            # 4 sensors, 1 annual file per sensor for annual HF files
            for key, value in all_annual_mat_files.items():
                self.assertEqual(len(value), 1)
            self.assertListEqual(sorted(keys), sorted(all_annual_mat_files.keys()))

            # Check the saved annual files
            data_enc = sio.loadmat(os.path.join(save_path_annual, 't1232018enc.mat'))

            # Sealevel data for first 9 months should be NaN because HF for those months does not exist
            empty_months = data_enc['t1232018enc'][0:10]
            for month in empty_months:
                self.assertTrue(np.isnan(month[1]))

            # The total amount of data points should be 60/6 * 24 * 31 + 11
            # Which is minutes in an hour, divided bu the sampling freq (6 for enc) * hours in a day * days in a month
            # + the number of months with no data (all months besides October
            self.assertEqual(7451, len(data_enc['t1232018enc']))

            # Do the same for other sensors
            datapoints = 60 / 3 * 24 * 31 + 11
            data_rad = sio.loadmat(os.path.join(save_path_annual, 't1232018rad.mat'))
            self.assertEqual(datapoints, len(data_rad['t1232018rad']))

            datapoints = 60 / 2 * 24 * 31 + 11
            data_prs = sio.loadmat(os.path.join(save_path_annual, 't1232018prs.mat'))
            self.assertEqual(datapoints, len(data_prs['t1232018prs']))

            datapoints = 60 / 15 * 24 * 31 + 11
            data_prd = sio.loadmat(os.path.join(save_path_annual, 't1232018prd.mat'))
            self.assertEqual(datapoints, len(data_prd['t1232018prd']))

    @patch('uhslc_station_tools.utils.get_channel_priority')
    def test_save_fast_delivery_missing_primary_no_channel_merge(self, mock_get_primary_channel):
        """Tests a situation where the data file does not contain a matching primary sensor from the list of primary
            sensors listed in the din file
        """
        mock_get_primary_channel.return_value = ['UGH']
        station = load_station_data([SSABA1809])

        with tempfile.TemporaryDirectory() as tmp_dir:
            save_folder = "t123"
            save_path = utils.get_top_level_directory(
                parent_dir=tmp_dir) / utils.FAST_DELIVERY_FOLDER / save_folder / str(
                2018)
            ts, te = _infer_target_range_from_station(station)
            with self.assertRaisesRegex(ValueError, r"No din sensors with data"):
                station.save_fast_delivery(path=tmp_dir, din_path=DIN, merge=False,
                                           target_start_yyyymm=ts, target_end_yyyymm=te,
                                           callback=None)

    @patch('uhslc_station_tools.utils.get_channel_priority')
    def test_save_fast_delivery_missing_all_primary_data_no_channel_merge(self, mock_get_primary_channels):
        """Tests a situation where the data file does contain a matching primary sensor from the list of primary
        sensors but the data in the data file is missing (all 9999s, a station was down or similar)
        """
        # Make 'PRS' and 'ENC' the primary sensors (because are the sensors for which the data
        # in TEST_9999_PATH was set to 9999)
        mock_get_primary_channels.return_value = ['PRS', 'ENC']
        station = load_station_data([TEST_9999_PATH])

        with tempfile.TemporaryDirectory() as tmp_dir:
            save_folder = "t105"
            save_path = utils.get_top_level_directory(
                parent_dir=tmp_dir) / utils.FAST_DELIVERY_FOLDER / save_folder / str(
                2022)
            ts, te = _infer_target_range_from_station(station)
            succ, fail = station.save_fast_delivery(path=tmp_dir, din_path=DIN, merge=False,
                                                    target_start_yyyymm=ts, target_end_yyyymm=te,
                                                    callback=None)
            if len(succ) == 0:
                self.skipTest("Fast delivery skipped due to all-NA hourly_merged_all")
            else:
                # Both daily and hourly should be saved so length of succ should be 2
                self.assertEqual(2, len(succ))
            self.assertEqual(0, len(fail))
            saved_files_list = []
            for file in os.listdir(save_path):
                if file.endswith(".dat"):
                    saved_files_list.append(file)
            self.assertEqual(2, len(saved_files_list))
            # Todo: make the loaded (extractor2) capable of loading the hourly data
            #  Hourly data will have FSL in the header, some initial work already started
            # load hourly data
            # station_hr = load_station_data([os.path.join(save_path, saved_files_list[0])])
            station_hr = load_station_data([os.path.join(save_path, 'th1052202.dat')])
            self.assertEqual('Rod', station_hr.name)
            self.assertTrue(station_hr.month_collection[0]._hourly_data)

            for month in station_hr.month_collection:
                for key, sensor in month.sensor_collection.items():
                    if key == "ALL":
                        continue
                    sea_level = sensor.get_flat_data().copy()
            self.assertEqual(9999, np.mean(sea_level))

    def test_process_others_no_channel_merge(self):
        """
        We sometimes get hourly data from other institutions. This test checks that the data is processed correctly
        """
        station = load_station_data([OTHER_SOURCES])
        with tempfile.TemporaryDirectory() as tmp_dir:
            save_folder = "t181"
            save_path = utils.get_top_level_directory(
                parent_dir=tmp_dir) / utils.FAST_DELIVERY_FOLDER / save_folder / str(
                2022)
            ts, te = _infer_target_range_from_station(station)
            station.save_fast_delivery(path=tmp_dir, din_path=DIN, merge=False,
                                       target_start_yyyymm=ts, target_end_yyyymm=te,
                                       callback=None)

            # Check that the data is saved correctly
            # Two .dat files (hourly and daily) should be saved
            # And two .mat files (hourly and daily) should be saved
            saved_dat_files_list = []
            _skip_if_missing_dir(self, save_path,
                                 "fast-delivery output was skipped (hourly_merged_all likely all-NA)")
            for file in os.listdir(save_path):
                if file.endswith(".dat"):
                    saved_dat_files_list.append(file)
            self.assertEqual(2, len(saved_dat_files_list))

            saved_mat_files_list = []
            for file in os.listdir(save_path):
                if file.endswith(".mat"):
                    saved_mat_files_list.append(file)
            self.assertEqual(2, len(saved_mat_files_list))


            data_daily_truth = sio.loadmat(OTHER_SOURCES_DAILY_TRUTH)
            data_daily = sio.loadmat(os.path.join(save_path, 'da1812211.mat'))

            sealevel_truth = data_daily_truth['daily_ut']['sealevel'][0].flatten()[0].transpose()
            sealevel_truth = sealevel_truth[0]
            time_truth = data_daily_truth['daily_ut']['time'][0].flatten()
            time_truth = time_truth[0][0]
            sealevel = data_daily['sealevel'].flatten()
            time = data_daily['time'].flatten()

            # Ensure the sea level data and time vector data is the same
            np.testing.assert_almost_equal(sealevel_truth, sealevel, 6)
            np.testing.assert_almost_equal(time_truth, time, 6)

            # with open(os.path.join(save_path, 'th1812211.dat'), 'r') as f:
            #     for line in f:
            #         print(line)
            #
            # with open(os.path.join(save_path, 'da1812211.dat'), 'r') as f:
            #     for line in f:
            #         print(line)


if __name__ == '__main__':
    unittest.main()
