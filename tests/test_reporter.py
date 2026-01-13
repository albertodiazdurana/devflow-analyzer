"""Tests for LLM reporter."""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.llm_reporter import LLMReporter, ReportSection, CICDReport
from src.models import BuildAnalysisResult, Bottleneck, ProjectMetrics


@pytest.fixture
def sample_analysis_result():
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
            Bottleneck("builds in slow-project", 500.0, 100),
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


class TestReportSection:
    """Tests for ReportSection dataclass."""

    def test_creation(self):
        """Test creating a report section."""
        section = ReportSection(
            title="Build Health",
            content="The builds are healthy.",
        )
        assert section.title == "Build Health"
        assert section.content == "The builds are healthy."


class TestCICDReport:
    """Tests for CICDReport dataclass."""

    def test_to_markdown(self):
        """Test markdown formatting."""
        report = CICDReport(
            build_health=ReportSection("Build Health Summary", "Builds are healthy."),
            bottleneck_analysis=ReportSection("Bottleneck Analysis", "No major bottlenecks."),
            failure_patterns=ReportSection("Failure Patterns", "Failures are low."),
            recommendations=ReportSection("Recommendations", "1. Keep monitoring."),
        )

        md = report.to_markdown()

        assert "# CI/CD Build Analysis Report" in md
        assert "## Build Health Summary" in md
        assert "Builds are healthy." in md
        assert "## Bottleneck Analysis" in md
        assert "## Failure Patterns" in md
        assert "## Recommendations" in md


class TestLLMReporter:
    """Tests for LLMReporter class."""

    def test_init_defaults(self):
        """Test default initialization."""
        reporter = LLMReporter()
        assert reporter.model_key == "claude-sonnet"
        assert reporter.temperature == 0.7
        assert reporter._llm is None

    def test_init_custom(self):
        """Test custom initialization."""
        reporter = LLMReporter(model_key="gpt-4o", temperature=0.3)
        assert reporter.model_key == "gpt-4o"
        assert reporter.temperature == 0.3

    def test_prompts_dir_exists(self):
        """Test that prompts directory is correctly set."""
        reporter = LLMReporter()
        assert reporter.PROMPTS_DIR.exists()

    def test_load_prompt_build_health(self):
        """Test loading build health prompt."""
        reporter = LLMReporter()
        prompt = reporter._load_prompt("build_health_summary")

        assert "metrics" in prompt.input_variables
        assert "{metrics}" in prompt.template

    def test_load_prompt_recommendations(self):
        """Test loading recommendations prompt (has analysis variable)."""
        reporter = LLMReporter()
        prompt = reporter._load_prompt("recommendations")

        assert "metrics" in prompt.input_variables
        assert "analysis" in prompt.input_variables

    def test_load_prompt_not_found(self):
        """Test loading nonexistent prompt raises."""
        reporter = LLMReporter()

        with pytest.raises(FileNotFoundError):
            reporter._load_prompt("nonexistent_prompt")

    @patch("src.llm_reporter.create_llm")
    def test_llm_lazy_loading(self, mock_create_llm):
        """Test that LLM is lazily loaded."""
        mock_llm = MagicMock()
        mock_create_llm.return_value = mock_llm

        reporter = LLMReporter()
        assert reporter._llm is None

        # Access llm property
        llm = reporter.llm

        assert llm == mock_llm
        mock_create_llm.assert_called_once_with("claude-sonnet", 0.7)

        # Second access shouldn't create new LLM
        llm2 = reporter.llm
        assert mock_create_llm.call_count == 1

    @patch("src.llm_reporter.create_llm")
    def test_generate_section(self, mock_create_llm, sample_analysis_result):
        """Test generating a single section."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="Generated content")
        mock_create_llm.return_value = mock_llm

        reporter = LLMReporter()

        # Mock the chain behavior
        with patch.object(reporter, '_generate_section', return_value="Test output"):
            result = reporter.generate_section("build_health_summary", sample_analysis_result)

        assert result == "Test output"

    @patch("src.llm_reporter.create_llm")
    def test_generate_report(self, mock_create_llm, sample_analysis_result):
        """Test generating full report."""
        mock_llm = MagicMock()
        mock_create_llm.return_value = mock_llm

        reporter = LLMReporter()

        # Mock _generate_section to return predictable content
        with patch.object(reporter, '_generate_section') as mock_gen:
            mock_gen.side_effect = [
                "Health summary content",
                "Bottleneck content",
                "Failure content",
                "Recommendations content",
            ]

            report = reporter.generate_report(sample_analysis_result)

        assert isinstance(report, CICDReport)
        assert report.build_health.content == "Health summary content"
        assert report.bottleneck_analysis.content == "Bottleneck content"
        assert report.failure_patterns.content == "Failure content"
        assert report.recommendations.content == "Recommendations content"

    def test_all_prompts_loadable(self):
        """Test that all expected prompts can be loaded."""
        reporter = LLMReporter()
        prompt_names = [
            "build_health_summary",
            "bottleneck_analysis",
            "failure_patterns",
            "recommendations",
        ]

        for name in prompt_names:
            prompt = reporter._load_prompt(name)
            assert prompt is not None
            assert "metrics" in prompt.input_variables
