"""Tests for DevFlow agent."""

from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from src.agent import (
    DevFlowAgent,
    set_analysis_context,
    analyze_bottlenecks,
    analyze_failures,
    compare_projects,
    get_summary_stats,
    _current_analysis,
)
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
            Bottleneck("builds in another-slow", 400.0, 50),
        ],
        projects_at_risk=["risky-project", "another-risky"],
        top_failing_projects=[
            ProjectMetrics(
                project="failing-project",
                n_builds=100,
                success_rate=0.5,
                failure_rate=0.4,
                error_rate=0.1,
                median_duration_seconds=200.0,
                p90_duration_seconds=500.0,
            ),
            ProjectMetrics(
                project="another-failing",
                n_builds=80,
                success_rate=0.6,
                failure_rate=0.35,
                error_rate=0.05,
                median_duration_seconds=150.0,
                p90_duration_seconds=400.0,
            ),
        ],
        project_metrics=[
            ProjectMetrics(
                project="project-a",
                n_builds=300,
                success_rate=0.9,
                failure_rate=0.08,
                error_rate=0.02,
                median_duration_seconds=120.0,
                p90_duration_seconds=300.0,
            ),
            ProjectMetrics(
                project="project-b",
                n_builds=200,
                success_rate=0.7,
                failure_rate=0.25,
                error_rate=0.05,
                median_duration_seconds=200.0,
                p90_duration_seconds=450.0,
            ),
        ],
    )


class TestSetAnalysisContext:
    """Tests for context setting."""

    def test_set_context(self, sample_analysis_result):
        """Test setting analysis context."""
        set_analysis_context(sample_analysis_result)
        # Context should be set (tested via tools)
        result = get_summary_stats.invoke({})
        assert "1,000" in result  # n_builds formatted


class TestAnalyzeBottlenecksTool:
    """Tests for analyze_bottlenecks tool."""

    def test_with_bottlenecks(self, sample_analysis_result):
        """Test analyzing bottlenecks when present."""
        set_analysis_context(sample_analysis_result)
        result = analyze_bottlenecks.invoke({})

        assert "Bottleneck Analysis" in result
        assert "slow-project" in result
        assert "500s" in result or "500" in result
        assert "baseline" in result

    def test_without_bottlenecks(self):
        """Test when no bottlenecks present."""
        no_bottleneck_result = BuildAnalysisResult(
            n_builds=100,
            n_projects=1,
            date_range_start=None,
            date_range_end=None,
            overall_success_rate=0.95,
            overall_failure_rate=0.05,
            overall_error_rate=0.0,
            median_duration_seconds=60.0,
            p90_duration_seconds=90.0,
            max_duration_seconds=120.0,
            bottlenecks=[],
        )
        set_analysis_context(no_bottleneck_result)
        result = analyze_bottlenecks.invoke({})

        assert "No significant bottlenecks" in result


class TestAnalyzeFailuresTool:
    """Tests for analyze_failures tool."""

    def test_with_failures(self, sample_analysis_result):
        """Test analyzing failures when present."""
        set_analysis_context(sample_analysis_result)
        result = analyze_failures.invoke({})

        assert "Failure Pattern Analysis" in result
        assert "75.0%" in result  # success rate
        assert "20.0%" in result  # failure rate
        assert "failing-project" in result
        assert "Projects at Risk" in result

    def test_status_distribution(self, sample_analysis_result):
        """Test status distribution in output."""
        set_analysis_context(sample_analysis_result)
        result = analyze_failures.invoke({})

        assert "passed" in result
        assert "failed" in result
        assert "750" in result or "75.0%" in result


class TestCompareProjectsTool:
    """Tests for compare_projects tool."""

    def test_with_projects(self, sample_analysis_result):
        """Test comparing projects."""
        set_analysis_context(sample_analysis_result)
        result = compare_projects.invoke({})

        assert "Project Comparison" in result
        assert "project-a" in result or "project-b" in result
        assert "Builds" in result
        assert "Success" in result

    def test_table_format(self, sample_analysis_result):
        """Test that output is in table format."""
        set_analysis_context(sample_analysis_result)
        result = compare_projects.invoke({})

        assert "|" in result  # Table separator
        assert "---" in result  # Table header separator


class TestGetSummaryStatsTool:
    """Tests for get_summary_stats tool."""

    def test_returns_llm_context(self, sample_analysis_result):
        """Test that summary stats returns LLM context."""
        set_analysis_context(sample_analysis_result)
        result = get_summary_stats.invoke({})

        assert "CI/CD Build Analysis Results" in result
        assert "1,000" in result
        assert "75.0%" in result


class TestDevFlowAgent:
    """Tests for DevFlowAgent class."""

    def test_init_defaults(self):
        """Test default initialization."""
        agent = DevFlowAgent()
        assert agent.model_key == "gpt-4o-mini"
        assert agent.temperature == 0.3
        assert agent._agent is None

    def test_init_custom(self):
        """Test custom initialization."""
        agent = DevFlowAgent(model_key="claude-sonnet", temperature=0.5)
        assert agent.model_key == "claude-sonnet"
        assert agent.temperature == 0.5

    @patch("src.agent.create_llm")
    @patch("src.agent.create_react_agent")
    def test_agent_creation(self, mock_create_react, mock_create_llm):
        """Test agent creation."""
        mock_llm = MagicMock()
        mock_create_llm.return_value = mock_llm
        mock_graph = MagicMock()
        mock_create_react.return_value = mock_graph

        agent = DevFlowAgent()
        graph = agent.agent

        mock_create_llm.assert_called_once_with("gpt-4o-mini", 0.3)
        mock_create_react.assert_called_once()
        assert graph is not None

    @patch("src.agent.create_llm")
    @patch("src.agent.create_react_agent")
    def test_analyze_sets_context(self, mock_create_react, mock_create_llm, sample_analysis_result):
        """Test that analyze sets the analysis context."""
        mock_llm = MagicMock()
        mock_create_llm.return_value = mock_llm

        # Mock the graph that create_react_agent returns
        mock_message = MagicMock()
        mock_message.content = "Test output"
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = {"messages": [mock_message]}
        mock_create_react.return_value = mock_graph

        agent = DevFlowAgent()
        result = agent.analyze(sample_analysis_result)

        assert result == "Test output"

    @patch("src.agent.create_llm")
    @patch("src.agent.create_react_agent")
    def test_investigate_custom_question(self, mock_create_react, mock_create_llm, sample_analysis_result):
        """Test investigating a custom question."""
        mock_llm = MagicMock()
        mock_create_llm.return_value = mock_llm

        # Mock the graph that create_react_agent returns
        mock_message = MagicMock()
        mock_message.content = "Investigation result"
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = {"messages": [mock_message]}
        mock_create_react.return_value = mock_graph

        agent = DevFlowAgent()
        result = agent.investigate(sample_analysis_result, "Why is project X failing?")

        assert result == "Investigation result"
        mock_graph.invoke.assert_called_once()
        call_args = mock_graph.invoke.call_args[0][0]
        # langgraph uses messages format with tuples
        assert call_args["messages"][0] == ("user", "Why is project X failing?")
