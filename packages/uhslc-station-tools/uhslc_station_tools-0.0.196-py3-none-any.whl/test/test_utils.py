import os
import unittest

import numpy as np

import uhslc_station_tools
from uhslc_station_tools import utils
from uhslc_station_tools.filtering import calwts
from uhslc_station_tools.utils import get_missing_months
from test.test_dat_file_save import DIN


class TestUtils(unittest.TestCase):
    def test_consecutive(self):
        sensor_months = {'bub': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], 'prd': [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                         'prs': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], 'rad': [1, 2, 3, 6, 7, 8, 9, 11, 12]}
        missing_bub = get_missing_months(sensor_months['bub'])
        missing_prd = get_missing_months(sensor_months['prd'])
        missing_prs = get_missing_months(sensor_months['prs'])
        missing_rad = get_missing_months(sensor_months['rad'])
        self.assertEqual(missing_bub, [])
        self.assertEqual(missing_prd, [1])
        self.assertEqual(missing_prs, [12])
        self.assertEqual(missing_rad, [4, 5, 10])

    def test_data_loading_validation(self):
        files1 = ['t1231811.dat', 't1231812.dat']
        files2 = ['t1231812.dat', 't1231901.dat']
        files3 = ['t1231904.dat', 't1231906.dat']

        self.assertTrue(utils.is_valid_files(files1))
        self.assertTrue(utils.is_valid_files(files2))
        self.assertFalse(utils.is_valid_files(files3))

    def test_get_primary_channels(self):
        primary_sensor = utils.get_channel_priority(DIN, '737')
        ps2 = utils.get_channel_priority(DIN, '001')
        ps3 = utils.get_channel_priority(DIN, '655')
        self.assertEqual(3, len(primary_sensor))
        self.assertEqual('BUB', primary_sensor[0])
        self.assertEqual('HOU', ps2[0])
        self.assertEqual(2, len(ps2))
        self.assertEqual('RAD', ps3[0])
        self.assertEqual(3, len(ps3))

    def test_hourly_daily_weights_function(self):
        dirname = os.path.dirname(__file__)
        file_path = os.path.join(dirname, 'test_data', 'filt_wts.txt')
        # load the legacy filter weights file
        filt_wts = []
        with open(file_path, "r") as file:
            for line in file:
                filt_wts.append(float(line))

        filt_wts = np.asarray(filt_wts)
        wts = np.concatenate((np.flip(filt_wts[-59:], 0), filt_wts), axis=0)

        # calculate the weight for hourly to daily data
        Tc = 60  # filter cutoff period = 60 hr (2.5 days)
        S = 119  # filter length = 119 hr (~5 days, must be odd)
        wts_calculated = np.asarray(calwts(Tc, S))
        np.testing.assert_array_almost_equal(wts_calculated, wts, decimal=5)


if __name__ == '__main__':
    unittest.main()
