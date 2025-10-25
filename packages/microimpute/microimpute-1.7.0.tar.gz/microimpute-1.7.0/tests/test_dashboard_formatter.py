"""Comprehensive tests for dashboard_formatter module.

This module tests the format_csv and save_formatted_csv functions
to ensure correct data formatting for dashboard visualization.
"""

import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from microimpute.utils.dashboard_formatter import format_csv


# Valid type values that should appear in the output
VALID_TYPES = {
    "benchmark_loss",
    "distribution_distance",
    "predictor_correlation",
    "predictor_target_mi",
    "predictor_importance",
    "progressive_inclusion",
}

# Expected columns in the output DataFrame
EXPECTED_COLUMNS = [
    "type",
    "method",
    "variable",
    "quantile",
    "metric_name",
    "metric_value",
    "split",
    "additional_info",
]


@pytest.fixture
def sample_autoimpute_result():
    """Create sample autoimpute result for testing."""
    return {
        "cv_results": {
            "OLS": {
                "quantile_loss": {
                    "results": pd.DataFrame(
                        {
                            0.1: [0.01, 0.02],
                            0.5: [0.015, 0.025],
                            0.9: [0.02, 0.03],
                        },
                        index=["train", "test"],
                    ),
                    "mean_train": 0.015,
                    "mean_test": 0.025,
                    "variables": ["var1", "var2"],
                },
                "log_loss": {
                    "results": pd.DataFrame(
                        {
                            0.5: [0.1, 0.15],
                        },
                        index=["train", "test"],
                    ),
                    "mean_train": 0.1,
                    "mean_test": 0.15,
                    "variables": ["cat_var"],
                },
            },
            "QRF": {
                "quantile_loss": {
                    "results": pd.DataFrame(
                        {
                            0.1: [0.012, 0.022],
                            0.5: [0.017, 0.027],
                            0.9: [0.022, 0.032],
                        },
                        index=["train", "test"],
                    ),
                    "mean_train": 0.017,
                    "mean_test": 0.027,
                    "variables": ["var1", "var2"],
                },
            },
        }
    }


@pytest.fixture
def sample_distribution_comparison():
    """Create sample distribution comparison DataFrame."""
    return pd.DataFrame(
        {
            "Variable": ["var1", "var2"],
            "Metric": ["wasserstein_distance", "wasserstein_distance"],
            "Distance": [0.05, 0.03],
        }
    )


@pytest.fixture
def sample_predictor_correlations():
    """Create sample predictor correlations dictionary."""
    predictors = ["pred1", "pred2", "pred3"]
    targets = ["target1", "target2"]

    return {
        "pearson": pd.DataFrame(
            [[1.0, 0.7, 0.3], [0.7, 1.0, 0.4], [0.3, 0.4, 1.0]],
            index=predictors,
            columns=predictors,
        ),
        "spearman": pd.DataFrame(
            [[1.0, 0.65, 0.25], [0.65, 1.0, 0.35], [0.25, 0.35, 1.0]],
            index=predictors,
            columns=predictors,
        ),
        "mutual_info": pd.DataFrame(
            [[1.0, 0.6, 0.2], [0.6, 1.0, 0.3], [0.2, 0.3, 1.0]],
            index=predictors,
            columns=predictors,
        ),
        "predictor_target_mi": pd.DataFrame(
            [[0.5, 0.3], [0.6, 0.4], [0.2, 0.1]],
            index=predictors,
            columns=targets,
        ),
    }


@pytest.fixture
def sample_predictor_importance():
    """Create sample predictor importance DataFrame."""
    return pd.DataFrame(
        {
            "predictor_removed": ["pred1", "pred2", "pred3"],
            "avg_quantile_loss": [0.02, 0.025, 0.018],
            "avg_log_loss": [0.1, 0.12, 0.08],
            "loss_increase": [0.005, 0.01, 0.003],
            "relative_impact": [5.0, 10.0, 3.0],
        }
    )


@pytest.fixture
def sample_progressive_inclusion():
    """Create sample progressive inclusion DataFrame."""
    return pd.DataFrame(
        {
            "step": [1, 2, 3],
            "predictor_added": ["pred2", "pred1", "pred3"],
            "predictors_included": [
                ["pred2"],
                ["pred2", "pred1"],
                ["pred2", "pred1", "pred3"],
            ],
            "avg_quantile_loss": [0.025, 0.018, 0.015],
            "avg_log_loss": [0.12, 0.09, 0.08],
            "cumulative_improvement": [0.0, 0.007, 0.010],
            "marginal_improvement": [0.0, 0.007, 0.003],
        }
    )


class TestFormatCSVBasic:
    """Basic tests for format_csv function."""

    def test_empty_inputs_returns_empty_dataframe(self):
        """Test that empty inputs return an empty DataFrame with correct columns."""
        result = format_csv()

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == EXPECTED_COLUMNS
        assert len(result) == 0

    def test_output_has_correct_columns(self, sample_autoimpute_result):
        """Test that output has all expected columns."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            output_path = f.name

        try:
            result = format_csv(
                output_path=output_path,
                autoimpute_result=sample_autoimpute_result,
            )

            assert list(result.columns) == EXPECTED_COLUMNS
        finally:
            Path(output_path).unlink()

    def test_all_types_are_valid(
        self,
        sample_autoimpute_result,
        sample_distribution_comparison,
        sample_predictor_correlations,
        sample_predictor_importance,
        sample_progressive_inclusion,
    ):
        """Test that all type values are from the valid set."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            output_path = f.name

        try:
            result = format_csv(
                output_path=output_path,
                autoimpute_result=sample_autoimpute_result,
                distribution_comparison_df=sample_distribution_comparison,
                predictor_correlations=sample_predictor_correlations,
                predictor_importance_df=sample_predictor_importance,
                progressive_inclusion_df=sample_progressive_inclusion,
                best_method_name="OLS",
            )

            unique_types = set(result["type"].unique())
            assert unique_types.issubset(
                VALID_TYPES
            ), f"Invalid types found: {unique_types - VALID_TYPES}"
            assert len(unique_types) > 0
        finally:
            Path(output_path).unlink()

    def test_metric_values_are_numeric(
        self, sample_autoimpute_result, sample_distribution_comparison
    ):
        """Test that metric_value column contains numeric values."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            output_path = f.name

        try:
            result = format_csv(
                output_path=output_path,
                autoimpute_result=sample_autoimpute_result,
                distribution_comparison_df=sample_distribution_comparison,
            )

            assert pd.api.types.is_numeric_dtype(result["metric_value"])
            assert not result["metric_value"].isna().any()
        finally:
            Path(output_path).unlink()

    def test_additional_info_is_valid_json(
        self, sample_autoimpute_result, sample_progressive_inclusion
    ):
        """Test that additional_info contains valid JSON."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            output_path = f.name

        try:
            result = format_csv(
                output_path=output_path,
                autoimpute_result=sample_autoimpute_result,
                progressive_inclusion_df=sample_progressive_inclusion,
            )

            # Try to parse each additional_info value as JSON
            for info in result["additional_info"]:
                try:
                    parsed = json.loads(info)
                    assert isinstance(parsed, dict)
                except json.JSONDecodeError:
                    pytest.fail(f"Invalid JSON in additional_info: {info}")
        finally:
            Path(output_path).unlink()


class TestFormatCSVBenchmarkLoss:
    """Tests for benchmark_loss type formatting."""

    def test_benchmark_loss_from_autoimpute(self, sample_autoimpute_result):
        """Test benchmark loss formatting from autoimpute results."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            output_path = f.name

        try:
            result = format_csv(
                output_path=output_path,
                autoimpute_result=sample_autoimpute_result,
            )

            benchmark_rows = result[result["type"] == "benchmark_loss"]
            assert len(benchmark_rows) > 0

            # Check that both methods are present
            methods = benchmark_rows["method"].unique()
            assert "OLS" in methods
            assert "QRF" in methods

            # Check that split values are valid
            splits = benchmark_rows["split"].unique()
            assert all(split in ["train", "test"] for split in splits)

            # Check quantile values
            quantiles = benchmark_rows["quantile"].unique()
            assert "mean" in quantiles  # Mean should be present
            numeric_quantiles = [
                q for q in quantiles if isinstance(q, (int, float))
            ]
            assert all(
                0 <= q <= 1 for q in numeric_quantiles
            )  # Valid quantile range
        finally:
            Path(output_path).unlink()

    def test_best_method_marked_correctly(self, sample_autoimpute_result):
        """Test that best method has correct suffix."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            output_path = f.name

        try:
            result = format_csv(
                output_path=output_path,
                autoimpute_result=sample_autoimpute_result,
                best_method_name="OLS",
            )

            benchmark_rows = result[result["type"] == "benchmark_loss"]

            # Check that OLS has _best_method suffix
            ols_rows = benchmark_rows[
                benchmark_rows["method"].str.contains("OLS")
            ]
            assert all(
                "_best_method" in method for method in ols_rows["method"]
            )

            # Check that QRF does not have the suffix
            qrf_rows = benchmark_rows[
                benchmark_rows["method"].str.contains("QRF")
            ]
            assert all(
                "_best_method" not in method for method in qrf_rows["method"]
            )
        finally:
            Path(output_path).unlink()


class TestFormatCSVDistributionDistance:
    """Tests for distribution_distance type formatting."""

    def test_distribution_distance_formatting(
        self, sample_distribution_comparison
    ):
        """Test distribution distance formatting."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            output_path = f.name

        try:
            result = format_csv(
                output_path=output_path,
                distribution_comparison_df=sample_distribution_comparison,
                best_method_name="OLS",
            )

            dist_rows = result[result["type"] == "distribution_distance"]
            assert len(dist_rows) == 2  # Two variables

            # Check variables are present
            assert set(dist_rows["variable"]) == {"var1", "var2"}

            # Check metric name is formatted correctly
            assert all(
                metric == "wasserstein_distance"
                for metric in dist_rows["metric_name"]
            )

            # Check split is 'full'
            assert all(split == "full" for split in dist_rows["split"])

            # Check quantile is 'N/A'
            assert all(q == "N/A" for q in dist_rows["quantile"])
        finally:
            Path(output_path).unlink()


class TestFormatCSVPredictorCorrelations:
    """Tests for predictor_correlation and predictor_target_mi types."""

    def test_predictor_correlation_formatting(
        self, sample_predictor_correlations
    ):
        """Test predictor correlation formatting."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            output_path = f.name

        try:
            result = format_csv(
                output_path=output_path,
                predictor_correlations=sample_predictor_correlations,
            )

            corr_rows = result[result["type"] == "predictor_correlation"]

            # Check that correlation types are present
            metric_names = set(corr_rows["metric_name"])
            assert "pearson" in metric_names
            assert "spearman" in metric_names
            assert "mutual_info" in metric_names

            # Check that additional_info contains predictor2
            for info in corr_rows["additional_info"]:
                parsed = json.loads(info)
                assert "predictor2" in parsed

            # Check that only upper triangle is included (no duplicates)
            # For 3 predictors, should have 3 pairs: (1,2), (1,3), (2,3)
            # Times 3 correlation types = 9 rows
            assert len(corr_rows) == 9
        finally:
            Path(output_path).unlink()

    def test_predictor_target_mi_formatting(
        self, sample_predictor_correlations
    ):
        """Test predictor-target MI formatting."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            output_path = f.name

        try:
            result = format_csv(
                output_path=output_path,
                predictor_correlations=sample_predictor_correlations,
            )

            mi_rows = result[result["type"] == "predictor_target_mi"]

            # Should have 3 predictors × 2 targets = 6 rows
            assert len(mi_rows) == 6

            # Check metric name
            assert all(
                metric == "mutual_info" for metric in mi_rows["metric_name"]
            )

            # Check additional_info contains target
            for info in mi_rows["additional_info"]:
                parsed = json.loads(info)
                assert "target" in parsed
                assert parsed["target"] in ["target1", "target2"]
        finally:
            Path(output_path).unlink()


class TestFormatCSVPredictorImportance:
    """Tests for predictor_importance type formatting."""

    def test_predictor_importance_formatting(
        self, sample_predictor_importance
    ):
        """Test predictor importance formatting."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            output_path = f.name

        try:
            result = format_csv(
                output_path=output_path,
                predictor_importance_df=sample_predictor_importance,
                best_method_name="OLS",
            )

            imp_rows = result[result["type"] == "predictor_importance"]

            # Should have 3 predictors × 2 metrics = 6 rows
            assert len(imp_rows) == 6

            # Check metric names
            metric_names = set(imp_rows["metric_name"])
            assert metric_names == {"relative_impact", "loss_increase"}

            # Check that all predictors are present
            variables = imp_rows["variable"].unique()
            assert set(variables) == {"pred1", "pred2", "pred3"}

            # Check split is 'test'
            assert all(split == "test" for split in imp_rows["split"])
        finally:
            Path(output_path).unlink()


class TestFormatCSVProgressiveInclusion:
    """Tests for progressive_inclusion type formatting."""

    def test_progressive_inclusion_formatting(
        self, sample_progressive_inclusion
    ):
        """Test progressive inclusion formatting."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            output_path = f.name

        try:
            result = format_csv(
                output_path=output_path,
                progressive_inclusion_df=sample_progressive_inclusion,
                best_method_name="OLS",
            )

            prog_rows = result[result["type"] == "progressive_inclusion"]

            # Should have 3 steps × 2 metrics = 6 rows
            assert len(prog_rows) == 6

            # Check metric names
            metric_names = set(prog_rows["metric_name"])
            assert metric_names == {
                "cumulative_improvement",
                "marginal_improvement",
            }

            # Check additional_info contains step and predictor_added
            for info in prog_rows["additional_info"]:
                parsed = json.loads(info)
                assert "step" in parsed
                assert "predictor_added" in parsed
                assert parsed["step"] in [1, 2, 3]
                assert parsed["predictor_added"] in ["pred1", "pred2", "pred3"]

            # Check that steps are in order for cumulative improvement
            cumulative_rows = prog_rows[
                prog_rows["metric_name"] == "cumulative_improvement"
            ]
            steps = [
                json.loads(info)["step"]
                for info in cumulative_rows["additional_info"]
            ]
            assert steps == sorted(steps)  # Should be in ascending order
        finally:
            Path(output_path).unlink()

    def test_progressive_inclusion_step_ordering(
        self, sample_progressive_inclusion
    ):
        """Test that steps are correctly numbered and ordered."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            output_path = f.name

        try:
            result = format_csv(
                output_path=output_path,
                progressive_inclusion_df=sample_progressive_inclusion,
            )

            prog_rows = result[result["type"] == "progressive_inclusion"]

            # Extract steps from additional_info
            steps = []
            for info in prog_rows["additional_info"]:
                parsed = json.loads(info)
                steps.append(parsed["step"])

            # Steps should be 1, 2, 3 (repeated for each metric)
            unique_steps = sorted(set(steps))
            assert unique_steps == [1, 2, 3]
        finally:
            Path(output_path).unlink()


class TestSaveFormattedCSV:
    """Tests for CSV file saving via format_csv."""

    def test_format_csv_creates_file(self, sample_autoimpute_result):
        """Test that format_csv creates a file when output_path is provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.csv"

            df = format_csv(
                output_path=str(output_path),
                autoimpute_result=sample_autoimpute_result,
            )

            # File should be created
            assert output_path.exists()

            # Verify content can be read back
            loaded_df = pd.read_csv(output_path)
            assert len(loaded_df) == len(df)
            assert list(loaded_df.columns) == EXPECTED_COLUMNS

    def test_saved_csv_preserves_data(self, sample_autoimpute_result):
        """Test that saved CSV preserves data correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.csv"

            df = format_csv(
                output_path=str(output_path),
                autoimpute_result=sample_autoimpute_result,
            )

            # Read back and compare
            loaded_df = pd.read_csv(output_path)

            # Check that numeric values are preserved
            assert np.allclose(
                df["metric_value"].values,
                loaded_df["metric_value"].values,
                rtol=1e-10,
            )

            # Check that string columns are preserved
            assert list(df["type"]) == list(loaded_df["type"])
            assert list(df["method"]) == list(loaded_df["method"])


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_none_values_handled_correctly(self):
        """Test that None values for optional parameters work."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            output_path = f.name

        try:
            result = format_csv(
                output_path=output_path,
                autoimpute_result=None,
                comparison_metrics_df=None,
                distribution_comparison_df=None,
                predictor_correlations=None,
                predictor_importance_df=None,
                progressive_inclusion_df=None,
                best_method_name=None,
            )

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0
        finally:
            Path(output_path).unlink()

    def test_empty_dataframes_handled_correctly(self):
        """Test that empty DataFrames are handled gracefully."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            output_path = f.name

        try:
            result = format_csv(
                output_path=output_path,
                distribution_comparison_df=pd.DataFrame(),
                predictor_importance_df=pd.DataFrame(),
                progressive_inclusion_df=pd.DataFrame(),
            )

            assert isinstance(result, pd.DataFrame)
            # Should have correct columns even with empty input
            assert list(result.columns) == EXPECTED_COLUMNS
        finally:
            Path(output_path).unlink()

    def test_mixed_quantile_types(self, sample_autoimpute_result):
        """Test that mixed quantile types (numeric and string) are handled."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            output_path = f.name

        try:
            result = format_csv(
                output_path=output_path,
                autoimpute_result=sample_autoimpute_result,
            )

            # Check that we have both numeric quantiles and 'mean'
            quantiles = result["quantile"].unique()
            has_numeric = any(
                isinstance(q, (int, float)) and not pd.isna(q)
                for q in quantiles
            )
            has_mean = "mean" in quantiles

            assert has_numeric
            assert has_mean
        finally:
            Path(output_path).unlink()
