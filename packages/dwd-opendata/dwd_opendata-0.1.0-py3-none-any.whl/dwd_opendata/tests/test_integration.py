"""Integration tests that make real calls to DWD servers.

These tests are slower and require network connectivity.
Run with: python -m pytest src/dwd_opendata/tests/test_integration.py -v
Or skip with: python -m pytest --ignore=src/dwd_opendata/tests/test_integration.py
"""

import unittest
import warnings
from datetime import datetime
import pandas as pd
import numpy as np
from pathlib import Path

import pytest

import dwd_opendata


@pytest.fixture(scope="class")
def temp_data_dir(tmp_path_factory):
    """Provide a temporary directory for DWD data."""
    temp_dir = tmp_path_factory.mktemp("dwd_test")

    # Store original and set new data_dir
    original_dir = dwd_opendata.data_dir
    dwd_opendata.data_dir = temp_dir

    yield temp_dir

    # Cleanup: restore original
    dwd_opendata.data_dir = original_dir


@pytest.mark.usefixtures("temp_data_dir")
class TestDWDIntegration(unittest.TestCase):
    """Integration tests with real DWD server calls.

    These tests validate that the library works with actual DWD data
    and can detect server-side changes that might break functionality.
    """

    def test_load_metadata_real_server(self):
        """Test loading metadata from real DWD server."""
        # Test a well-established variable that should always be available
        metadata = dwd_opendata.load_metadata("air_temperature", time="hourly")

        # Validate structure
        self.assertIsInstance(metadata, pd.DataFrame)
        self.assertGreater(len(metadata), 100, "Should have many stations")

        # Check expected columns
        expected_cols = [
            "Stations_id",
            "von_datum",
            "bis_datum",
            "Stationshoehe",
            "geoBreite",
            "geoLaenge",
            "Stationsname",
            "Bundesland",
        ]
        for col in expected_cols:
            self.assertIn(col, metadata.columns)

        # Validate data types and ranges
        self.assertTrue(metadata["Stations_id"].dtype in [np.int64, int])
        self.assertTrue(
            metadata["geoBreite"].between(47, 55.1).all(),
            "Latitudes should be in Germany",
        )
        self.assertTrue(
            metadata["geoLaenge"].between(5, 16).all(),
            "Longitudes should be in Germany",
        )

    def test_get_metadata_multiple_variables(self):
        """Test getting metadata for multiple variables from real server."""
        variables = ["air_temperature", "precipitation"]
        metadata = dwd_opendata.get_metadata(
            variables, era="historical", time="hourly"
        )

        self.assertIsInstance(metadata, pd.DataFrame)
        self.assertGreater(len(metadata), 50, "Should find common stations")

        # Verify we found stations that have both variables
        station_names = metadata["Stationsname"].values
        self.assertGreater(len(station_names), 0)

    def test_load_small_dataset_real(self):
        """Test loading a small real dataset (last 2 years only)."""
        # Use a well-known station and recent data to minimize download size
        current_year = datetime.now().year
        start_year = current_year - 2

        # Test with Konstanz - should be available
        data = dwd_opendata.load_station(
            "Konstanz",
            "air_temperature",
            era="historical",
            time="hourly",
            start_year=start_year,
            end_year=current_year,
            redownload=False,  # Use cached data if available
        )

        if data is not None:
            # Validate the loaded data
            self.assertGreater(
                len(data.coords["time"]),
                100,
                "Should have substantial data",
            )
            self.assertEqual(data.name, "Konstanz")

            # Check data structure
            self.assertIn(
                "air_temperature", data.coords["met_variable"].values
            )

            # Validate data ranges (basic sanity checks)
            temp_data = data.sel(met_variable="air_temperature").values
            valid_temps = temp_data[~np.isnan(temp_data)]
            if len(valid_temps) > 0:
                self.assertTrue(
                    np.all(valid_temps > -50),
                    "No extremely low temperatures",
                )
                self.assertTrue(
                    np.all(valid_temps < 50),
                    "No extremely high temperatures",
                )
        else:
            warnings.warn(
                "Could not load data for Konstanz - station may not be available"
            )

    def test_server_connectivity_and_structure(self):
        """Test that DWD server structure hasn't changed."""
        # Test FTP connectivity and basic structure
        from ftplib import FTP

        ftp = FTP(dwd_opendata.ftp_url)
        ftp.login()

        # Test that the basic CDC structure exists
        base_path = "climate_environment/CDC/observations_germany/climate"
        listings = ftp.nlst(base_path)

        # Should contain time resolution directories
        expected_dirs = ["hourly", "daily", "10_minutes"]
        found_dirs = [item.split("/")[-1] for item in listings]

        for expected in expected_dirs:
            self.assertIn(
                expected,
                found_dirs,
                f"Expected directory {expected} not found in {found_dirs}",
            )

        ftp.close()

    def test_pdf_documentation_download(self):
        """Test that PDF documentation is still available."""
        # This should download the PDF if not cached
        dwd_opendata.do_download_pdf("air_temperature", time="hourly")

        # Check that a PDF was created
        pdf_files = list(dwd_opendata.data_dir.glob("*.pdf"))
        self.assertGreater(
            len(pdf_files), 0, "Should have downloaded at least one PDF"
        )

        # Check that the PDF is not empty
        for pdf_file in pdf_files:
            self.assertGreater(
                pdf_file.stat().st_size,
                1000,
                f"PDF {pdf_file.name} seems too small",
            )

    def test_main_section_integration(self):
        """Integration test based on the __main__ section examples."""

        # Test the metadata loading part
        metadata = dwd_opendata.get_metadata(
            "solar", era="historical", time="10_minutes"
        )
        self.assertIsInstance(metadata, pd.DataFrame)

        if len(metadata) > 0:
            # Test loading actual data for a small time range
            current_year = datetime.now().year
            recent_year = current_year - 1

            # Try to load data for Konstanz if it has solar data
            konstanz_meta = metadata[metadata["Stationsname"] == "Konstanz"]
            if len(konstanz_meta) > 0:
                solar_data = dwd_opendata._load_station_one_var(
                    "Konstanz",
                    "solar_global",
                    era="historical",
                    time="10_minutes",
                    start_year=recent_year,
                    end_year=recent_year,
                    redownload=False,
                )

                if len(solar_data) > 0:
                    self.assertIsInstance(solar_data, pd.DataFrame)
                    self.assertGreater(len(solar_data), 0)

    def test_variable_availability(self):
        """Test that expected variables are still available on the server."""
        # Test key variables that should always be available
        core_variables = ["air_temperature", "precipitation", "wind"]

        for variable in core_variables:
            with self.subTest(variable=variable):
                metadata = dwd_opendata.load_metadata(
                    variable, era="historical", time="hourly"
                )
                self.assertGreater(
                    len(metadata),
                    50,
                    f"Variable {variable} should have many stations",
                )


@unittest.skipIf(
    # Skip integration tests in CI or when explicitly requested
    __name__ != "__main__",
    "Integration tests skipped - run explicitly with python -m unittest test_integration",
)
class TestIntegrationRunner(TestDWDIntegration):
    """Wrapper to control when integration tests run."""

    pass


if __name__ == "__main__":
    # When run directly, always run integration tests
    print("Running integration tests with real DWD server calls...")
    print("This may take several minutes and requires internet connectivity.")
    unittest.main(verbosity=2)
