"""SDMetrics-based evaluation."""

import logging
from typing import Dict, Optional, Union

import numpy as np
import pandas as pd
from sdmetrics.reports.single_table import QualityReport
from sdmetrics.single_table import (
    ContingencySimilarity,
    CorrelationSimilarity,
    KSComplement,
    TVComplement,
)
from sdv.metadata import SingleTableMetadata

logger = logging.getLogger(__name__)


class SDMetricsEvaluator:
    """Comprehensive evaluation using SDMetrics library."""

    def __init__(self, metadata: Optional[Union[dict, SingleTableMetadata]] = None):
        """
        Initialize evaluator.

        Parameters
        ----------
        metadata : dict or SingleTableMetadata, optional
            SDV metadata for the dataset
        """
        self.metadata = metadata
        self.results: Dict[str, float] = {}

    def evaluate_all(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        metadata: Optional[Union[dict, SingleTableMetadata]] = None,
    ) -> Dict[str, float]:
        """
        Run comprehensive evaluation.

        Parameters
        ----------
        real_data : pd.DataFrame
            Real training data
        synthetic_data : pd.DataFrame
            Generated synthetic data
        metadata : dict, optional
            Override metadata

        Returns
        -------
        dict
            Dictionary of metric scores
        """
        logger.info("Running SDMetrics evaluation...")

        results = {}

        # Overall Quality Report
        results.update(self._quality_report(real_data, synthetic_data, metadata))

        # Statistical Fidelity
        results.update(self._statistical_metrics(real_data, synthetic_data))

        # Column-wise metrics
        results.update(self._column_metrics(real_data, synthetic_data))

        self.results = results
        return results

    def _quality_report(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        metadata: Optional[Union[dict, SingleTableMetadata]] = None,
    ) -> Dict[str, float]:
        """Generate overall quality report."""
        try:
            meta_input = metadata or self.metadata
            if meta_input is None:
                meta = SingleTableMetadata()
                meta.detect_from_dataframe(real_data)
            elif isinstance(meta_input, SingleTableMetadata):
                meta = meta_input
                # Ensure metadata is detected if not already done
                try:
                    meta.detect_from_dataframe(real_data)
                except Exception:
                    # Metadata already detected, continue
                    pass
            else:
                # meta_input is a dict
                meta = meta_input

            report = QualityReport()
            # Convert metadata to dict if it's a SingleTableMetadata object
            if hasattr(meta, "to_dict"):
                meta_dict = meta.to_dict()  # type: ignore
            else:
                meta_dict = meta
            report.generate(real_data, synthetic_data, meta_dict)

            properties_df = report.get_properties()
            properties_scores = properties_df.set_index("Property")["Score"]

            return {
                "quality_score": report.get_score(),
                "column_shapes_score": properties_scores["Column Shapes"],
                "column_pair_trends_score": properties_scores["Column Pair Trends"],
            }
        except Exception as e:
            logger.warning(f"Quality report failed: {e}")
            return {}

    def _statistical_metrics(
        self, real_data: pd.DataFrame, synthetic_data: pd.DataFrame
    ) -> Dict[str, float]:
        """Compute statistical similarity metrics."""
        results = {}

        # Kolmogorov-Smirnov Complement
        try:
            ks_scores = []
            for col in real_data.select_dtypes(include=[np.number]).columns:
                score = KSComplement.compute(
                    real_data=real_data[[col]],  # Pass as DataFrame
                    synthetic_data=synthetic_data[[col]],
                )
                ks_scores.append(score)

            if ks_scores:
                results["ks_complement_mean"] = np.mean(ks_scores)
                results["ks_complement_std"] = np.std(ks_scores)
        except Exception as e:
            logger.warning(f"KS test failed: {e}")

        # Total Variation Distance
        try:
            tv_scores = []
            for col in real_data.select_dtypes(include=["object", "category"]).columns:
                score = TVComplement.compute(
                    real_data=real_data[[col]],  # Pass as DataFrame
                    synthetic_data=synthetic_data[[col]],
                )
                tv_scores.append(score)

            if tv_scores:
                results["tv_complement_mean"] = np.mean(tv_scores)
        except Exception as e:
            logger.warning(f"TV distance failed: {e}")

        # Correlation Similarity
        try:
            corr_score = CorrelationSimilarity.compute(
                real_data=real_data, synthetic_data=synthetic_data
            )
            results["correlation_similarity"] = corr_score
        except Exception as e:
            logger.warning(f"Correlation similarity failed: {e}")

        # Contingency Similarity (for categorical pairs)
        try:
            cat_cols = real_data.select_dtypes(include=["object", "category"]).columns.tolist()
            if len(cat_cols) >= 2:
                cont_score = ContingencySimilarity.compute(
                    real_data=real_data, synthetic_data=synthetic_data
                )
                results["contingency_similarity"] = cont_score
        except Exception as e:
            logger.warning(f"Contingency similarity failed: {e}")

        return results

    def _column_metrics(
        self, real_data: pd.DataFrame, synthetic_data: pd.DataFrame
    ) -> Dict[str, float]:
        """Compute per-column quality metrics."""
        results = {}

        # Basic statistics comparison
        for col in real_data.columns:
            try:
                if pd.api.types.is_numeric_dtype(real_data[col]):
                    real_mean = real_data[col].mean()
                    synth_mean = synthetic_data[col].mean()
                    real_std = real_data[col].std()
                    synth_std = synthetic_data[col].std()

                    results[f"{col}_mean_diff"] = abs(real_mean - synth_mean) / (real_std + 1e-8)
                    results[f"{col}_std_ratio"] = synth_std / (real_std + 1e-8)
            except Exception as e:
                logger.warning(f"Column metric failed for {col}: {e}")

        return results

    def get_summary(self) -> pd.DataFrame:
        """Get summary of key metrics as DataFrame."""
        if not self.results:
            return pd.DataFrame()

        summary_metrics = {
            k: v
            for k, v in self.results.items()
            if not k.startswith("_") and isinstance(v, (int, float))
        }

        return pd.DataFrame([summary_metrics]).T.rename(columns={0: "Score"})
