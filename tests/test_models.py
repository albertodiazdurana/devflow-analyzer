"""Tests for data models."""

import json
from datetime import datetime

import pytest

from src.models import BuildEvent, Bottleneck, ProjectMetrics, BuildAnalysisResult


class TestBuildEvent:
    """Tests for BuildEvent dataclass."""

    def test_to_dict_with_datetime(self):
        """Test serialization with datetime."""
        event = BuildEvent(
            build_id="123",
            project="test-project",
            status="passed",
            duration_seconds=120.5,
            started_at=datetime(2024, 1, 15, 10, 30, 0),
            language="java",
            tests_run=50,
            tests_failed=0,
        )
        d = event.to_dict()

        assert d["build_id"] == "123"
        assert d["project"] == "test-project"
        assert d["status"] == "passed"
        assert d["duration_seconds"] == 120.5
        assert d["started_at"] == "2024-01-15T10:30:00"
        assert d["language"] == "java"
        assert d["tests_run"] == 50
        assert d["tests_failed"] == 0

    def test_to_dict_with_none_datetime(self):
        """Test serialization with None datetime."""
        event = BuildEvent(
            build_id="456",
            project="test-project",
            status="failed",
            duration_seconds=None,
            started_at=None,
        )
        d = event.to_dict()

        assert d["started_at"] is None
        assert d["duration_seconds"] is None


class TestBottleneck:
    """Tests for Bottleneck dataclass."""

    def test_to_dict(self):
        """Test serialization."""
        bottleneck = Bottleneck(
            transition="build → test",
            avg_wait_seconds=45.5,
            frequency=100,
        )
        d = bottleneck.to_dict()

        assert d["transition"] == "build → test"
        assert d["avg_wait_seconds"] == 45.5
        assert d["frequency"] == 100


class TestProjectMetrics:
    """Tests for ProjectMetrics dataclass."""

    def test_to_dict(self):
        """Test serialization."""
        metrics = ProjectMetrics(
            project="my-project",
            n_builds=500,
            success_rate=0.85,
            failure_rate=0.10,
            error_rate=0.05,
            median_duration_seconds=120.0,
            p90_duration_seconds=300.0,
            avg_tests_run=150.5,
            avg_tests_failed=2.3,
        )
        d = metrics.to_dict()

        assert d["project"] == "my-project"
        assert d["n_builds"] == 500
        assert d["success_rate"] == 0.85
        assert d["failure_rate"] == 0.10
        assert d["error_rate"] == 0.05


class TestBuildAnalysisResult:
    """Tests for BuildAnalysisResult dataclass."""

    @pytest.fixture
    def sample_result(self):
        """Create a sample BuildAnalysisResult for testing."""
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
            status_counts={"passed": 750, "failed": 200, "errored": 50},
            language_counts={"java": 800, "python": 200},
            bottlenecks=[
                Bottleneck("build → test", 45.0, 100),
                Bottleneck("test → deploy", 120.0, 50),
            ],
            projects_at_risk=["risky-project"],
            top_failing_projects=[
                ProjectMetrics(
                    project="failing-project",
                    n_builds=100,
                    success_rate=0.5,
                    failure_rate=0.4,
                    error_rate=0.1,
                    median_duration_seconds=200.0,
                    p90_duration_seconds=500.0,
                )
            ],
            project_metrics=[],
        )

    def test_to_dict(self, sample_result):
        """Test dictionary serialization."""
        d = sample_result.to_dict()

        assert d["n_builds"] == 1000
        assert d["n_projects"] == 5
        assert d["date_range_start"] == "2024-01-01T00:00:00"
        assert d["date_range_end"] == "2024-06-30T00:00:00"
        assert d["overall_success_rate"] == 0.75
        assert len(d["bottlenecks"]) == 2
        assert d["bottlenecks"][0]["transition"] == "build → test"

    def test_to_json(self, sample_result):
        """Test JSON serialization."""
        json_str = sample_result.to_json()
        parsed = json.loads(json_str)

        assert parsed["n_builds"] == 1000
        assert parsed["overall_success_rate"] == 0.75

    def test_to_llm_context(self, sample_result):
        """Test LLM context formatting."""
        context = sample_result.to_llm_context()

        assert "# CI/CD Build Analysis Results" in context
        assert "Total builds analyzed: 1,000" in context
        assert "Success rate: 75.0%" in context
        assert "Failure rate: 20.0%" in context
        assert "## Bottlenecks" in context
        assert "build → test" in context
        assert "## Projects at Risk" in context
        assert "risky-project" in context

    def test_to_llm_context_empty_bottlenecks(self):
        """Test LLM context with no bottlenecks."""
        result = BuildAnalysisResult(
            n_builds=100,
            n_projects=1,
            date_range_start=None,
            date_range_end=None,
            overall_success_rate=1.0,
            overall_failure_rate=0.0,
            overall_error_rate=0.0,
            median_duration_seconds=60.0,
            p90_duration_seconds=90.0,
            max_duration_seconds=120.0,
        )
        context = result.to_llm_context()

        assert "## Bottlenecks" not in context
        assert "## Projects at Risk" not in context
