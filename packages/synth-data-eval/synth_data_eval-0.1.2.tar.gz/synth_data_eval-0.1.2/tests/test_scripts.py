"""Tests for scripts."""

import shutil
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from scripts.download_datasets import DatasetDownloader


class TestDatasetDownloader:
    """Test dataset downloader."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_initialization(self, temp_data_dir):
        """Test downloader initialization."""
        downloader = DatasetDownloader(data_dir=str(temp_data_dir))
        assert downloader.data_dir == temp_data_dir
        assert temp_data_dir.exists()

    def test_download_diabetes(self, temp_data_dir):
        """Test diabetes dataset download."""
        downloader = DatasetDownloader(data_dir=str(temp_data_dir))
        downloader.download_diabetes()

        output_path = temp_data_dir / "diabetes.csv"
        assert output_path.exists()

        # Check that file contains data
        df = pd.read_csv(output_path)
        assert len(df) > 0
        assert len(df.columns) > 0

    def test_download_adult(self, temp_data_dir):
        """Test adult dataset download."""
        downloader = DatasetDownloader(data_dir=str(temp_data_dir))
        downloader.download_adult()

        output_path = temp_data_dir / "adult.csv"
        assert output_path.exists()

        # Check that file contains data
        df = pd.read_csv(output_path)
        assert len(df) > 0
        assert "income" in df.columns
        assert df["income"].isin([0, 1]).all()

    def test_download_credit_handles_errors(self, temp_data_dir):
        """Test credit download handles network errors gracefully."""
        downloader = DatasetDownloader(data_dir=str(temp_data_dir))

        # This should not raise an exception even if download fails
        try:
            downloader.download_credit()
        except Exception:
            pytest.fail("download_credit should handle errors gracefully")

    def test_download_all(self, temp_data_dir):
        """Test downloading all datasets."""
        downloader = DatasetDownloader(data_dir=str(temp_data_dir))
        downloader.download_all()

        # Check that expected files exist
        expected_files = ["adult.csv", "diabetes.csv"]
        for filename in expected_files:
            assert (temp_data_dir / filename).exists()
