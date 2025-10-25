"""Download and prepare all datasets for evaluation."""

import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatasetDownloader:
    """Download and prepare evaluation datasets."""

    def __init__(self, data_dir: str = "datasets"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def download_all(self):
        """Download all datasets."""
        logger.info("Starting dataset downloads...")

        self.download_adult()
        self.download_credit()
        self.download_diabetes()

        logger.info("All datasets downloaded successfully!")

    def download_adult(self):
        """Download Adult Income dataset from UCI."""
        logger.info("Downloading Adult Income dataset...")

        url = (
            "https://archive.ics.uci.edu/ml/machine-learning-databases/" "adult/adult.data"
        )  # noqa: E501
        columns = [
            "age",
            "workclass",
            "fnlwgt",
            "education",
            "education_num",
            "marital_status",
            "occupation",
            "relationship",
            "race",
            "sex",
            "capital_gain",
            "capital_loss",
            "hours_per_week",
            "native_country",
            "income",
        ]

        df = pd.read_csv(url, names=columns, na_values=" ?", skipinitialspace=True)  # noqa: E501
        df = df.dropna()
        df["income"] = (df["income"] == ">50K").astype(int)

        output_path = self.data_dir / "adult.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"✓ Adult dataset saved: {df.shape}")

    def download_credit(self):
        """Download Credit Card Default dataset."""
        logger.info("Downloading Credit Card Default dataset...")

        # Using UCI default of credit card clients dataset
        url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00350/default%20of%20credit%20card%20clients.xls"  # noqa: E501

        try:
            df = pd.read_excel(url, header=1)
            df.columns = df.columns.str.lower().str.replace(" ", "_")

            output_path = self.data_dir / "credit.csv"
            df.to_csv(output_path, index=False)
            logger.info(f"✓ Credit dataset saved: {df.shape}")
        except Exception as e:
            logger.warning(f"Could not download credit dataset: {e}")
            logger.info("Please download manually from UCI ML Repository")

    def download_diabetes(self):
        """Download Diabetes dataset."""
        logger.info("Downloading Diabetes dataset...")

        from sklearn.datasets import load_diabetes

        data = load_diabetes(as_frame=True)
        df = data.frame

        output_path = self.data_dir / "diabetes.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"✓ Diabetes dataset saved: {df.shape}")


if __name__ == "__main__":
    downloader = DatasetDownloader()
    downloader.download_all()
