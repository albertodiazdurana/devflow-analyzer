"""Tests for agent + vector store retrieval integration."""

from datetime import datetime
from unittest.mock import patch, MagicMock

import chromadb
import pytest

from src.agent import (
    DevFlowAgent,
    search_historical_analyses,
    set_analysis_context,
    set_vector_store,
)
from src.models import BuildAnalysisResult, Bottleneck, ProjectMetrics
from src.vector_store import DevFlowVectorStore


@pytest.fixture
def sample_analysis():
    """Create a sample BuildAnalysisResult for testing."""
    return BuildAnalysisResult(
        n_builds=500,
        n_projects=5,
        date_range_start=datetime(2024, 1, 1),
        date_range_end=datetime(2024, 6, 30),
        overall_success_rate=0.82,
        overall_failure_rate=0.12,
        overall_error_rate=0.06,
        median_duration_seconds=180.0,
        p90_duration_seconds=450.0,
        max_duration_seconds=1200.0,
        status_counts={"passed": 410, "failed": 60, "errored": 30},
        language_counts={"python": 300, "java": 200},
        bottlenecks=[
            Bottleneck(transition="build → test", avg_wait_seconds=120.0, frequency=45),
        ],
        projects_at_risk=["project-alpha"],
        top_failing_projects=[
            ProjectMetrics(
                project="project-alpha",
                n_builds=100,
                success_rate=0.65,
                failure_rate=0.25,
                error_rate=0.10,
                median_duration_seconds=200.0,
                p90_duration_seconds=500.0,
            ),
        ],
        project_metrics=[],
    )


@pytest.fixture
def mock_embeddings():
    """Mock OpenAI embeddings to avoid API calls."""
    with patch("src.vector_store.OpenAIEmbeddings") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.embed_documents.return_value = [[0.1] * 10]
        mock_instance.embed_query.return_value = [0.1] * 10
        mock_cls.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def vector_store(mock_embeddings):
    """Create a DevFlowVectorStore with in-memory ChromaDB."""
    client = chromadb.Client()
    try:
        client.delete_collection(DevFlowVectorStore.COLLECTION_NAME)
    except Exception:
        pass
    store = DevFlowVectorStore(client=client)
    yield store
    try:
        client.delete_collection(DevFlowVectorStore.COLLECTION_NAME)
    except Exception:
        pass


class TestSearchHistoricalAnalysesTool:
    """Tests for the search_historical_analyses tool."""

    def test_no_vector_store(self):
        """Tool returns graceful message when no vector store is configured."""
        set_vector_store(None)
        result = search_historical_analyses.invoke({"query": "high failure rate"})
        assert "No historical data available" in result

    def test_empty_vector_store(self, vector_store):
        """Tool returns graceful message when vector store is empty."""
        set_vector_store(vector_store)
        result = search_historical_analyses.invoke({"query": "high failure rate"})
        assert "No historical analyses stored yet" in result

    def test_returns_results(self, vector_store, sample_analysis):
        """Tool returns historical analysis excerpts when data exists."""
        set_vector_store(vector_store)
        vector_store.store_analysis(sample_analysis, project_name="test-project")

        result = search_historical_analyses.invoke({"query": "failure rate"})
        assert "Historical Analysis 1" in result
        assert "test-project" in result
        assert "0.82" in result or "82" in result  # success_rate in metadata

    def test_formats_multiple_results(self, vector_store, sample_analysis):
        """Tool formats multiple results with separators."""
        set_vector_store(vector_store)
        vector_store.store_analysis(sample_analysis, project_name="proj-a")
        vector_store.store_analysis(sample_analysis, project_name="proj-b")

        result = search_historical_analyses.invoke({"query": "CI/CD analysis"})
        assert "Historical Analysis 1" in result
        assert "Historical Analysis 2" in result
        assert "---" in result  # separator between results


class TestDevFlowAgentVectorStoreIntegration:
    """Tests for DevFlowAgent with vector store."""

    def test_init_without_vector_store(self):
        """Agent works without vector store (backward compatibility)."""
        agent = DevFlowAgent()
        assert agent.vector_store is None

    def test_init_with_vector_store(self, vector_store):
        """Agent accepts vector store parameter."""
        agent = DevFlowAgent(vector_store=vector_store)
        assert agent.vector_store is vector_store

    @patch("src.agent.create_llm")
    @patch("src.agent.create_react_agent")
    def test_agent_has_five_tools(self, mock_create_react, mock_create_llm):
        """Agent should be created with 5 tools (including history search)."""
        mock_create_llm.return_value = MagicMock()
        mock_create_react.return_value = MagicMock()

        agent = DevFlowAgent()
        _ = agent.agent  # trigger lazy creation

        call_args = mock_create_react.call_args
        tools = call_args[0][1]  # second positional arg is tools list
        assert len(tools) == 5
        tool_names = [t.name for t in tools]
        assert "search_historical_analyses" in tool_names

    @patch("src.agent.create_llm")
    @patch("src.agent.create_react_agent")
    def test_analyze_stores_result(
        self, mock_create_react, mock_create_llm, vector_store, sample_analysis
    ):
        """Analyze should auto-store analysis in vector store."""
        mock_create_llm.return_value = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Analysis complete"
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = {"messages": [mock_message]}
        mock_create_react.return_value = mock_graph

        agent = DevFlowAgent(vector_store=vector_store)
        result = agent.analyze(sample_analysis)

        assert result == "Analysis complete"
        assert vector_store.count == 1

    @patch("src.agent.create_llm")
    @patch("src.agent.create_react_agent")
    def test_analyze_without_vector_store_skips_storage(
        self, mock_create_react, mock_create_llm, sample_analysis
    ):
        """Analyze without vector store should not attempt storage."""
        mock_create_llm.return_value = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Analysis complete"
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = {"messages": [mock_message]}
        mock_create_react.return_value = mock_graph

        agent = DevFlowAgent()  # no vector store
        result = agent.analyze(sample_analysis)

        assert result == "Analysis complete"

    @patch("src.agent.create_llm")
    @patch("src.agent.create_react_agent")
    def test_investigate_does_not_store(
        self, mock_create_react, mock_create_llm, vector_store, sample_analysis
    ):
        """Investigate should NOT auto-store (only analyze does)."""
        mock_create_llm.return_value = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Investigation result"
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = {"messages": [mock_message]}
        mock_create_react.return_value = mock_graph

        agent = DevFlowAgent(vector_store=vector_store)
        result = agent.investigate(sample_analysis, "Why is project X failing?")

        assert result == "Investigation result"
        assert vector_store.count == 0  # investigate doesn't store
