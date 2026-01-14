"""Tests for evaluation module."""

from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from src.evaluation import (
    EvaluationResult,
    compute_cost,
    compute_rouge_scores,
    ExperimentTracker,
    Timer,
    ABTestResult,
)
from src.models import BuildAnalysisResult


class TestEvaluationResult:
    """Tests for EvaluationResult dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = EvaluationResult(
            model_key="gpt-4o-mini",
            latency_ms=1500.0,
            input_tokens=1000,
            output_tokens=500,
            cost_usd=0.00045,
            output_text="Test output",
            rouge_scores={
                "rouge1": {"precision": 0.8, "recall": 0.7, "fmeasure": 0.75},
                "rouge2": {"precision": 0.6, "recall": 0.5, "fmeasure": 0.55},
                "rougeL": {"precision": 0.7, "recall": 0.6, "fmeasure": 0.65},
            },
        )

        d = result.to_dict()

        assert d["model_key"] == "gpt-4o-mini"
        assert d["latency_ms"] == 1500.0
        assert d["input_tokens"] == 1000
        assert d["output_tokens"] == 500
        assert d["cost_usd"] == 0.00045
        assert d["rouge_1_f"] == 0.75
        assert d["rouge_2_f"] == 0.55
        assert d["rouge_l_f"] == 0.65

    def test_to_dict_empty_rouge(self):
        """Test dictionary conversion with no ROUGE scores."""
        result = EvaluationResult(
            model_key="gpt-4o-mini",
            latency_ms=1000.0,
            input_tokens=500,
            output_tokens=250,
            cost_usd=0.0002,
            output_text="Test",
            rouge_scores={},
        )

        d = result.to_dict()

        assert d["rouge_1_f"] == 0.0
        assert d["rouge_2_f"] == 0.0
        assert d["rouge_l_f"] == 0.0


class TestComputeCost:
    """Tests for cost computation."""

    def test_gpt4o_mini_cost(self):
        """Test cost calculation for GPT-4o-mini."""
        # GPT-4o-mini: $0.15/1M input, $0.60/1M output
        # = $0.00015/1K input, $0.0006/1K output
        cost = compute_cost("gpt-4o-mini", input_tokens=1000, output_tokens=1000)

        expected = 0.00015 + 0.0006  # $0.00075
        assert abs(cost - expected) < 0.0001

    def test_claude_sonnet_cost(self):
        """Test cost calculation for Claude Sonnet."""
        # Claude Sonnet: $3/1M input, $15/1M output
        # = $0.003/1K input, $0.015/1K output
        cost = compute_cost("claude-sonnet", input_tokens=1000, output_tokens=1000)

        expected = 0.003 + 0.015  # $0.018
        assert abs(cost - expected) < 0.0001

    def test_ollama_free(self):
        """Test that Ollama models are free."""
        cost = compute_cost("ollama-llama3", input_tokens=10000, output_tokens=5000)

        assert cost == 0.0

    def test_invalid_model(self):
        """Test error on invalid model."""
        with pytest.raises(ValueError, match="Unknown model"):
            compute_cost("invalid-model", 1000, 1000)


class TestComputeRougeScores:
    """Tests for ROUGE score computation."""

    def test_identical_texts(self):
        """Test ROUGE scores for identical texts."""
        text = "This is a test sentence for ROUGE scoring."
        scores = compute_rouge_scores(text, text)

        assert scores["rouge1"]["fmeasure"] == 1.0
        assert scores["rouge2"]["fmeasure"] == 1.0
        assert scores["rougeL"]["fmeasure"] == 1.0

    def test_different_texts(self):
        """Test ROUGE scores for different texts."""
        output = "The build failed due to test errors."
        reference = "Build failure caused by compilation issues."

        scores = compute_rouge_scores(output, reference)

        # Should have some overlap but not perfect
        assert 0 < scores["rouge1"]["fmeasure"] < 1
        assert scores["rouge1"]["precision"] > 0
        assert scores["rouge1"]["recall"] > 0

    def test_empty_output(self):
        """Test ROUGE with empty output."""
        scores = compute_rouge_scores("", "Reference text here.")

        assert scores["rouge1"]["fmeasure"] == 0.0
        assert scores["rouge2"]["fmeasure"] == 0.0

    def test_partial_overlap(self):
        """Test ROUGE with partial word overlap."""
        output = "The project has high failure rate of 50%"
        reference = "The project failure rate is high at 45%"

        scores = compute_rouge_scores(output, reference)

        # Should have significant overlap
        assert scores["rouge1"]["fmeasure"] > 0.5


class TestTimer:
    """Tests for Timer utility."""

    def test_timer_measures_time(self):
        """Test that timer measures elapsed time."""
        import time

        with Timer() as timer:
            time.sleep(0.1)  # Sleep 100ms

        assert timer.elapsed_ms >= 100
        assert timer.elapsed_ms < 200  # Should not take too long

    def test_timer_without_context(self):
        """Test timer returns 0 if not used as context."""
        timer = Timer()
        assert timer.elapsed_ms == 0.0


class TestExperimentTracker:
    """Tests for MLflow experiment tracking."""

    @patch("src.evaluation.mlflow")
    def test_init_sets_tracking(self, mock_mlflow):
        """Test tracker initializes MLflow correctly."""
        tracker = ExperimentTracker("test-experiment", "test-uri")

        mock_mlflow.set_tracking_uri.assert_called_once_with("test-uri")
        mock_mlflow.set_experiment.assert_called_once_with("test-experiment")

    @patch("src.evaluation.mlflow")
    def test_start_run_context(self, mock_mlflow):
        """Test start_run as context manager."""
        tracker = ExperimentTracker("test-experiment")

        with tracker.start_run("test-run", tags={"key": "value"}):
            pass

        mock_mlflow.start_run.assert_called_once_with(
            run_name="test-run", tags={"key": "value"}
        )

    @patch("src.evaluation.mlflow")
    def test_log_params(self, mock_mlflow):
        """Test logging parameters."""
        tracker = ExperimentTracker("test-experiment")

        with tracker.start_run("test-run"):
            tracker.log_params({"model": "gpt-4o-mini", "temperature": 0.3})

        mock_mlflow.log_params.assert_called_once_with(
            {"model": "gpt-4o-mini", "temperature": 0.3}
        )

    @patch("src.evaluation.mlflow")
    def test_log_metrics(self, mock_mlflow):
        """Test logging metrics."""
        tracker = ExperimentTracker("test-experiment")

        with tracker.start_run("test-run"):
            tracker.log_metrics({"latency_ms": 1500.0, "cost_usd": 0.001})

        mock_mlflow.log_metrics.assert_called_once_with(
            {"latency_ms": 1500.0, "cost_usd": 0.001}, step=None
        )

    @patch("src.evaluation.mlflow")
    def test_log_params_without_run_raises(self, mock_mlflow):
        """Test that logging without active run raises error."""
        tracker = ExperimentTracker("test-experiment")

        with pytest.raises(RuntimeError, match="No active run"):
            tracker.log_params({"key": "value"})


class TestABTestResult:
    """Tests for ABTestResult."""

    def test_summary_statistics(self):
        """Test summary statistics calculation."""
        results_a = [
            EvaluationResult(
                model_key="gpt-4o-mini",
                latency_ms=1000.0,
                input_tokens=500,
                output_tokens=250,
                cost_usd=0.0002,
                output_text="Output A1",
                rouge_scores={"rouge1": {"fmeasure": 0.8}},
            ),
            EvaluationResult(
                model_key="gpt-4o-mini",
                latency_ms=1200.0,
                input_tokens=500,
                output_tokens=250,
                cost_usd=0.0002,
                output_text="Output A2",
                rouge_scores={"rouge1": {"fmeasure": 0.7}},
            ),
        ]

        results_b = [
            EvaluationResult(
                model_key="claude-haiku",
                latency_ms=800.0,
                input_tokens=500,
                output_tokens=250,
                cost_usd=0.0005,
                output_text="Output B1",
                rouge_scores={"rouge1": {"fmeasure": 0.85}},
            ),
            EvaluationResult(
                model_key="claude-haiku",
                latency_ms=900.0,
                input_tokens=500,
                output_tokens=250,
                cost_usd=0.0005,
                output_text="Output B2",
                rouge_scores={"rouge1": {"fmeasure": 0.9}},
            ),
        ]

        ab_result = ABTestResult(
            variant_a="GPT-4o-mini",
            variant_b="Claude Haiku",
            results_a=results_a,
            results_b=results_b,
        )

        summary = ab_result.summary()

        assert summary["variant_a"]["name"] == "GPT-4o-mini"
        assert summary["variant_a"]["n_runs"] == 2
        assert summary["variant_a"]["latency_mean_ms"] == 1100.0
        assert summary["variant_a"]["rouge1_mean"] == 0.75

        assert summary["variant_b"]["name"] == "Claude Haiku"
        assert summary["variant_b"]["n_runs"] == 2
        assert summary["variant_b"]["latency_mean_ms"] == 850.0
        assert summary["variant_b"]["rouge1_mean"] == 0.875


class TestIntegration:
    """Integration tests for evaluation module."""

    @pytest.fixture
    def sample_analysis_result(self):
        """Create sample BuildAnalysisResult."""
        return BuildAnalysisResult(
            n_builds=1000,
            n_projects=5,
            date_range_start=datetime(2024, 1, 1),
            date_range_end=datetime(2024, 6, 30),
            overall_success_rate=0.75,
            overall_failure_rate=0.20,
            overall_error_rate=0.05,
            median_duration_seconds=180.0,
            p90_duration_seconds=450.0,
            max_duration_seconds=1200.0,
        )

    @patch("src.evaluation.mlflow")
    def test_log_evaluation_result(self, mock_mlflow, sample_analysis_result):
        """Test logging a complete EvaluationResult."""
        tracker = ExperimentTracker("test-experiment")

        result = EvaluationResult(
            model_key="gpt-4o-mini",
            latency_ms=1500.0,
            input_tokens=1000,
            output_tokens=500,
            cost_usd=0.00045,
            output_text="Analysis complete.",
            rouge_scores={"rouge1": {"fmeasure": 0.8}},
        )

        with tracker.start_run("test-run"):
            tracker.log_evaluation_result(result)

        # Check params logged
        mock_mlflow.log_params.assert_called_once()
        params_call = mock_mlflow.log_params.call_args[0][0]
        assert params_call["model_key"] == "gpt-4o-mini"

        # Check metrics logged
        mock_mlflow.log_metrics.assert_called_once()
        metrics_call = mock_mlflow.log_metrics.call_args[0][0]
        assert metrics_call["latency_ms"] == 1500.0
        assert metrics_call["cost_usd"] == 0.00045
