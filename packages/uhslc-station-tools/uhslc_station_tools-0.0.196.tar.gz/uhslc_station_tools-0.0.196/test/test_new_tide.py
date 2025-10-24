import os
import unittest
import numpy as np
from unittest.mock import patch
from uhslc_station_tools.extractor import load_station_data

class TestExtractor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Class level setup executed once."""
        cls.dirname = os.path.dirname(__file__)

    def setUp(self):
        """Setup test data and parameters for each test."""
        self.data_file = [os.path.join(self.dirname, 'test_data', 'monp', 'sacaj2401.dat')]
        self.expected_header = '82ACA'
        self.expected_level = '1645'
        self.expected_mean = 0.307885
        self.expected_std = 529.764967

    def test_extracting_new_tide(self):
        """Ensure new tide prediction data loads correctly and matches expected values."""
        station = load_station_data(self.data_file)
        new_tide = station.month_collection[0].sensor_collection.sensors['PRD']
        self.assertEqual(new_tide.header.split()[0], self.expected_header)
        self.assertEqual(new_tide.height, self.expected_level)
        self.assertAlmostEqual(np.mean(new_tide.data), self.expected_mean, places=3)
        self.assertAlmostEqual(np.std(new_tide.data), self.expected_std, places=3)

    @patch('uhslc_station_tools.extractor.open', side_effect=FileNotFoundError)
    def test_error_on_file_missing(self, mock_open):
        """Test error handling when the data file is missing."""
        with self.assertRaises(FileNotFoundError):
            load_station_data(['nonexistent_file.dat'])

if __name__ == '__main__':
    unittest.main()
