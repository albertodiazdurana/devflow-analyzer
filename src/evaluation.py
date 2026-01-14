"""Evaluation pipeline with MLflow tracking and metrics."""

import time
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Generator

import mlflow
from rouge_score import rouge_scorer

from .llm_provider import get_model_config, AVAILABLE_MODELS
from .models import BuildAnalysisResult


@dataclass
class EvaluationResult:
    """Result of evaluating an LLM output."""

    model_key: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    cost_usd: float
    output_text: str
    rouge_scores: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for logging."""
        return {
            "model_key": self.model_key,
            "latency_ms": self.latency_ms,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": self.cost_usd,
            "rouge_1_f": self.rouge_scores.get("rouge1", {}).get("fmeasure", 0.0),
            "rouge_2_f": self.rouge_scores.get("rouge2", {}).get("fmeasure", 0.0),
            "rouge_l_f": self.rouge_scores.get("rougeL", {}).get("fmeasure", 0.0),
        }


def compute_cost(model_key: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost in USD based on token usage.

    Args:
        model_key: Key from AVAILABLE_MODELS
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Cost in USD
    """
    config = get_model_config(model_key)
    input_cost = (input_tokens / 1000) * config.cost_per_1k_input
    output_cost = (output_tokens / 1000) * config.cost_per_1k_output
    return input_cost + output_cost


def compute_rouge_scores(output: str, reference: str) -> dict:
    """Compute ROUGE scores between output and reference.

    Args:
        output: Generated text
        reference: Reference text to compare against

    Returns:
        Dictionary with rouge1, rouge2, rougeL scores
    """
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    scores = scorer.score(reference, output)

    return {
        "rouge1": {
            "precision": scores["rouge1"].precision,
            "recall": scores["rouge1"].recall,
            "fmeasure": scores["rouge1"].fmeasure,
        },
        "rouge2": {
            "precision": scores["rouge2"].precision,
            "recall": scores["rouge2"].recall,
            "fmeasure": scores["rouge2"].fmeasure,
        },
        "rougeL": {
            "precision": scores["rougeL"].precision,
            "recall": scores["rougeL"].recall,
            "fmeasure": scores["rougeL"].fmeasure,
        },
    }


class ExperimentTracker:
    """MLflow wrapper for experiment tracking."""

    def __init__(self, experiment_name: str, tracking_uri: str = "mlruns"):
        """Initialize experiment tracker.

        Args:
            experiment_name: Name of the MLflow experiment
            tracking_uri: Path to MLflow tracking directory
        """
        self.experiment_name = experiment_name
        self.tracking_uri = tracking_uri
        self._run = None

        # Set up MLflow
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment_name)

    @contextmanager
    def start_run(
        self, run_name: str, tags: Optional[dict] = None
    ) -> Generator[None, None, None]:
        """Start an MLflow run as a context manager.

        Args:
            run_name: Name for this run
            tags: Optional tags to add to the run

        Yields:
            None (use tracker methods inside the context)
        """
        with mlflow.start_run(run_name=run_name, tags=tags) as run:
            self._run = run
            yield
            self._run = None

    def log_params(self, params: dict) -> None:
        """Log parameters to the current run.

        Args:
            params: Dictionary of parameter names and values
        """
        if self._run is None:
            raise RuntimeError("No active run. Use start_run() context manager.")
        mlflow.log_params(params)

    def log_metrics(self, metrics: dict, step: Optional[int] = None) -> None:
        """Log metrics to the current run.

        Args:
            metrics: Dictionary of metric names and values
            step: Optional step number for time-series metrics
        """
        if self._run is None:
            raise RuntimeError("No active run. Use start_run() context manager.")
        mlflow.log_metrics(metrics, step=step)

    def log_artifact(self, content: str, filename: str) -> None:
        """Log a text artifact to the current run.

        Args:
            content: Text content to save
            filename: Name for the artifact file
        """
        if self._run is None:
            raise RuntimeError("No active run. Use start_run() context manager.")

        # Write to temp file and log
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=Path(filename).suffix, delete=False
        ) as f:
            f.write(content)
            temp_path = f.name

        mlflow.log_artifact(temp_path, artifact_path="outputs")
        Path(temp_path).unlink()  # Clean up

    def log_evaluation_result(self, result: EvaluationResult) -> None:
        """Log an EvaluationResult to the current run.

        Args:
            result: EvaluationResult to log
        """
        metrics = result.to_dict()
        model_key = metrics.pop("model_key")

        self.log_params({"model_key": model_key})
        self.log_metrics(metrics)
        self.log_artifact(result.output_text, "output.md")


class Timer:
    """Simple timer for measuring latency."""

    def __init__(self):
        self._start = None
        self._end = None

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self._end = time.perf_counter()

    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        if self._start is None or self._end is None:
            return 0.0
        return (self._end - self._start) * 1000


@dataclass
class ABTestResult:
    """Result of an A/B test comparison."""

    variant_a: str
    variant_b: str
    results_a: list[EvaluationResult]
    results_b: list[EvaluationResult]

    def summary(self) -> dict:
        """Get summary statistics for comparison."""
        import statistics

        def stats(results: list[EvaluationResult]) -> dict:
            latencies = [r.latency_ms for r in results]
            costs = [r.cost_usd for r in results]
            rouge1 = [r.rouge_scores.get("rouge1", {}).get("fmeasure", 0) for r in results]

            return {
                "n_runs": len(results),
                "latency_mean_ms": statistics.mean(latencies) if latencies else 0,
                "latency_std_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0,
                "cost_mean_usd": statistics.mean(costs) if costs else 0,
                "rouge1_mean": statistics.mean(rouge1) if rouge1 else 0,
            }

        return {
            "variant_a": {"name": self.variant_a, **stats(self.results_a)},
            "variant_b": {"name": self.variant_b, **stats(self.results_b)},
        }


class ABTest:
    """A/B test framework for comparing prompts or models."""

    def __init__(
        self,
        experiment_name: str,
        variant_a_name: str,
        variant_b_name: str,
    ):
        """Initialize A/B test.

        Args:
            experiment_name: Name for the experiment
            variant_a_name: Label for variant A
            variant_b_name: Label for variant B
        """
        self.experiment_name = experiment_name
        self.variant_a_name = variant_a_name
        self.variant_b_name = variant_b_name
        self.tracker = ExperimentTracker(f"ab-test-{experiment_name}")

    def run_model_comparison(
        self,
        analysis_result: BuildAnalysisResult,
        model_a: str,
        model_b: str,
        task: str,
        n_runs: int = 3,
        reference: Optional[str] = None,
    ) -> ABTestResult:
        """Compare two models on the same task.

        Args:
            analysis_result: Data to analyze
            model_a: First model key
            model_b: Second model key
            task: Task/question for the agent
            n_runs: Number of runs per variant
            reference: Optional reference text for ROUGE

        Returns:
            ABTestResult with comparison data
        """
        from .agent import DevFlowAgent

        results_a = []
        results_b = []

        for i in range(n_runs):
            # Run variant A
            with self.tracker.start_run(
                f"{self.variant_a_name}-run-{i+1}",
                tags={"variant": "A", "model": model_a},
            ):
                result_a = self._run_agent(analysis_result, model_a, task, reference)
                self.tracker.log_evaluation_result(result_a)
                results_a.append(result_a)

            # Run variant B
            with self.tracker.start_run(
                f"{self.variant_b_name}-run-{i+1}",
                tags={"variant": "B", "model": model_b},
            ):
                result_b = self._run_agent(analysis_result, model_b, task, reference)
                self.tracker.log_evaluation_result(result_b)
                results_b.append(result_b)

        return ABTestResult(
            variant_a=self.variant_a_name,
            variant_b=self.variant_b_name,
            results_a=results_a,
            results_b=results_b,
        )

    def _run_agent(
        self,
        analysis_result: BuildAnalysisResult,
        model_key: str,
        task: str,
        reference: Optional[str] = None,
    ) -> EvaluationResult:
        """Run agent and collect metrics.

        Args:
            analysis_result: Data to analyze
            model_key: Model to use
            task: Task for the agent
            reference: Optional reference for ROUGE

        Returns:
            EvaluationResult with metrics
        """
        from .agent import DevFlowAgent

        agent = DevFlowAgent(model_key=model_key)

        with Timer() as timer:
            output = agent.investigate(analysis_result, task)

        # Estimate tokens (rough: 4 chars per token)
        input_tokens = len(task) // 4 + len(analysis_result.to_llm_context()) // 4
        output_tokens = len(output) // 4

        rouge_scores = {}
        if reference:
            rouge_scores = compute_rouge_scores(output, reference)

        return EvaluationResult(
            model_key=model_key,
            latency_ms=timer.elapsed_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=compute_cost(model_key, input_tokens, output_tokens),
            output_text=output,
            rouge_scores=rouge_scores,
        )
