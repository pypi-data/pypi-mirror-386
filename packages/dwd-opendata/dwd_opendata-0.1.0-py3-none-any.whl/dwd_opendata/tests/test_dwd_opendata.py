import unittest
from unittest.mock import patch, mock_open, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime
import tempfile
import os
from pathlib import Path

import dwd_opendata


class TestDWDOpenData(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures with temporary data directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_data_dir = dwd_opendata.data_dir
        dwd_opendata.data_dir = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        dwd_opendata.data_dir = self.original_data_dir

    def test_get_ftp_root(self):
        """Test FTP root path generation."""
        # Test default parameters
        root = dwd_opendata.get_ftp_root()
        expected = "climate_environment/CDC/observations_germany/climate/hourly/{variable}/historical"
        self.assertEqual(root, expected)

        # Test daily without era
        root = dwd_opendata.get_ftp_root(era=None, time="daily")
        expected = "climate_environment/CDC/observations_germany/climate/daily/{variable}"
        self.assertEqual(root, expected)

    def test_get_ftp_variable_root(self):
        """Test variable-specific FTP root path generation."""
        root = dwd_opendata.get_ftp_variable_root("solar")
        expected = "climate_environment/CDC/observations_germany/climate/hourly/solar/historical"
        self.assertEqual(root, expected)

    def test_shorten_compound_varnames_decorator(self):
        """Test the compound variable name shortening decorator."""
        @dwd_opendata.shorten_compound_varnames
        def test_func(variable):
            return variable

        # Test solar compound names are shortened
        result = test_func("solar_global")
        self.assertEqual(result, "solar")

        result = test_func("solar_diffuse")
        self.assertEqual(result, "solar")

        # Test non-solar variables pass through
        result = test_func("wind_speed")
        self.assertEqual(result, "wind_speed")

    def test_get_zip_filename(self):
        """Test ZIP filename generation for different time resolutions."""
        metadata = {"Stations_id": 433}

        # Test hourly
        filename = dwd_opendata.get_zip_filename("solar", time="hourly", **metadata)
        self.assertEqual(filename, "stundenwerte_ST_00433")

        # Test daily
        filename = dwd_opendata.get_zip_filename("air_temperature", time="daily", **metadata)
        self.assertEqual(filename, "tageswerte_KL_00433")

        # Test 10_minutes
        filename = dwd_opendata.get_zip_filename("solar", time="10_minutes", **metadata)
        self.assertEqual(filename, "10minutenwerte_SD_00433")

    def test_get_meta_filename(self):
        """Test metadata filename generation."""
        # Test hourly
        filename = dwd_opendata.get_meta_filename("ST", "hourly")
        expected = "ST_Stundenwerte_Beschreibung_Stationen.txt"
        self.assertEqual(filename, expected)

        # Test daily
        filename = dwd_opendata.get_meta_filename("KL", "daily")
        expected = "KL_Tageswerte_Beschreibung_Stationen.txt"
        self.assertEqual(filename, expected)

        # Test 10_minutes
        filename = dwd_opendata.get_meta_filename("SD", "10_minutes")
        expected = "zehn_min_sd_Beschreibung_Stationen.txt"
        self.assertEqual(filename, expected)

    def test_get_description_name(self):
        """Test PDF description filename generation."""
        # Test hourly
        name = dwd_opendata.get_description_name("ST", "hourly")
        expected = "DESCRIPTION_obsgermany-climate-hourly-st_en.pdf"
        self.assertEqual(name, expected)

        # Test 10_minutes
        name = dwd_opendata.get_description_name("SD", "10_minutes")
        expected = "DESCRIPTION_obsgermany-climate-10min-sd_en.pdf"
        self.assertEqual(name, expected)

    def test_variable_mappings(self):
        """Test variable mapping dictionaries are consistent."""
        # Test that all variables in variable_shorts have entries in found_in
        for time_res in ["hourly", "daily", "10_minutes"]:
            shorts = dwd_opendata.variable_shorts[time_res]
            found = dwd_opendata.found_in[time_res]

            for var in shorts.keys():
                self.assertIn(var, found,
                    f"Variable {var} missing from found_in[{time_res}]")

    @patch('dwd_opendata.pd.read_fwf')
    @patch('dwd_opendata.urlrequest.urlopen')
    def test_load_metadata(self, mock_urlopen, mock_read_fwf):
        """Test metadata loading functionality."""
        # Mock URL response
        mock_response = MagicMock()
        mock_response.read.return_value = b"mock metadata content"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Mock pandas DataFrame
        mock_df = pd.DataFrame({
            'Stations_id': [433, 434],
            'von_datum': [pd.Timestamp('1990-01-01'), pd.Timestamp('1995-01-01')],
            'bis_datum': [pd.Timestamp('2020-12-31'), pd.Timestamp('2020-12-31')],
            'Stationshoehe': [443.0, 500.0],
            'geoBreite': [47.6779, 48.0],
            'geoLaenge': [9.1732, 9.5],
            'Stationsname': ['Konstanz', 'Test Station'],
            'Bundesland': ['Baden-Wuerttemberg', 'Bayern']
        })
        mock_read_fwf.return_value = mock_df

        result = dwd_opendata.load_metadata("solar", time="hourly")

        # Verify function calls
        self.assertTrue(mock_urlopen.called)
        self.assertTrue(mock_read_fwf.called)

        # Check result structure
        self.assertIsInstance(result, pd.DataFrame)
        self.assertListEqual(list(result.columns), dwd_opendata.meta_header)

    def test_filter_metadata(self):
        """Test metadata filtering functionality."""
        # Create sample metadata
        metadata = pd.DataFrame({
            'Stations_id': [433, 434, 435],
            'von_datum': [pd.Timestamp('1990-01-01')] * 3,
            'bis_datum': [pd.Timestamp('2020-12-31')] * 3,
            'Stationshoehe': [443.0, 500.0, 600.0],
            'geoBreite': [47.6779, 48.0, 49.0],
            'geoLaenge': [9.1732, 9.5, 10.0],
            'Stationsname': ['Konstanz', 'Test1', 'Test2'],
            'Bundesland': ['Baden-Wuerttemberg', 'Bayern', 'Bayern']
        })

        # Test geographic filtering
        filtered = dwd_opendata.filter_metadata(
            metadata,
            lon_min=9.0,
            lon_max=9.6,
            lat_min=47.0,
            lat_max=48.5,
            start=pd.Timestamp('2000-01-01'),
            end=pd.Timestamp('2010-01-01')
        )

        # Should include Konstanz and Test1, exclude Test2
        self.assertEqual(len(filtered), 2)
        self.assertIn('Konstanz', filtered['Stationsname'].values)
        self.assertIn('Test1', filtered['Stationsname'].values)

    @patch('dwd_opendata.load_metadata')
    def test_get_metadata(self, mock_load_metadata):
        """Test getting metadata for multiple variables."""
        # Mock metadata for different variables
        mock_metadata = pd.DataFrame({
            'Stations_id': [433, 434],
            'von_datum': [pd.Timestamp('1990-01-01')] * 2,
            'bis_datum': [pd.Timestamp('2020-12-31')] * 2,
            'Stationshoehe': [443.0, 500.0],
            'geoBreite': [47.6779, 48.0],
            'geoLaenge': [9.1732, 9.5],
            'Stationsname': ['Konstanz', 'Test Station'],
            'Bundesland': ['Baden-Wuerttemberg', 'Bayern']
        })
        mock_load_metadata.return_value = mock_metadata

        result = dwd_opendata.get_metadata(["wind", "air_temperature"])

        # Verify calls for each variable
        self.assertEqual(mock_load_metadata.call_count, 2)
        self.assertIsInstance(result, pd.DataFrame)

    def test_main_section_examples(self):
        """Test that the examples from __main__ section would work with mocked data."""
        with patch('dwd_opendata.get_metadata') as mock_get_metadata, \
             patch('dwd_opendata._load_station_one_var') as mock_load_var, \
             patch('dwd_opendata.load_data') as mock_load_data, \
             patch('dwd_opendata.map_stations') as mock_map_stations:

            # Mock returns
            mock_get_metadata.return_value = pd.DataFrame()
            mock_load_var.return_value = pd.DataFrame()
            mock_load_data.return_value = MagicMock()
            mock_map_stations.return_value = (MagicMock(), MagicMock())

            # Test the examples from __main__
            start = datetime(1980, 1, 1)
            end = datetime(2016, 12, 31)
            variables = ("wind", "air_temperature", "sun", "precipitation")

            # These should not raise exceptions
            metadata = dwd_opendata.get_metadata("solar", time="10_minutes")
            solar = dwd_opendata._load_station_one_var(
                "Konstanz", "solar_global", time="10_minutes", redownload=False
            )

            fig, ax = dwd_opendata.map_stations(
                variables,
                lon_min=7,
                lat_min=47.4,
                lon_max=12.0,
                lat_max=49.0,
                start=start,
                end=end,
            )

            data = dwd_opendata.load_data(
                ("Konstanz", "Feldberg/Schwarzwald"),
                variables=variables,
                start_year=start,
                end_year=end,
            )

            # Verify mocks were called
            self.assertTrue(mock_get_metadata.called)
            self.assertTrue(mock_load_var.called)
            self.assertTrue(mock_map_stations.called)
            self.assertTrue(mock_load_data.called)


if __name__ == '__main__':
    unittest.main()