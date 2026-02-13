"""Tests for vector store module."""

from datetime import datetime
from unittest.mock import patch, MagicMock

import chromadb
import pytest

from src.models import BuildAnalysisResult, Bottleneck, ProjectMetrics
from src.vector_store import (
    DevFlowVectorStore,
    _make_doc_id,
    create_chroma_client,
    is_streamlit_cloud,
)


@pytest.fixture
def sample_analysis() -> BuildAnalysisResult:
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
        # Return a 10-dimensional fake embedding for any input
        mock_instance.embed_documents.return_value = [[0.1] * 10]
        mock_instance.embed_query.return_value = [0.1] * 10
        mock_cls.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def vector_store(mock_embeddings):
    """Create a DevFlowVectorStore with in-memory ChromaDB and mocked embeddings."""
    client = chromadb.Client()
    # Ensure clean state by deleting any leftover collection
    try:
        client.delete_collection(DevFlowVectorStore.COLLECTION_NAME)
    except Exception:
        pass
    store = DevFlowVectorStore(client=client)
    yield store
    # Cleanup after test
    try:
        client.delete_collection(DevFlowVectorStore.COLLECTION_NAME)
    except Exception:
        pass


class TestEnvironmentDetection:
    """Tests for cloud detection and client creation."""

    def test_is_not_streamlit_cloud(self):
        """Local environment should not be detected as cloud."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("os.path.exists", return_value=False):
                assert is_streamlit_cloud() is False

    def test_is_streamlit_cloud_env_var(self):
        """Detect cloud via STREAMLIT_SHARING_MODE env var."""
        with patch.dict("os.environ", {"STREAMLIT_SHARING_MODE": "1"}):
            assert is_streamlit_cloud() is True

    def test_is_streamlit_cloud_mount(self):
        """Detect cloud via /mount/src path."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("os.path.exists", return_value=True):
                assert is_streamlit_cloud() is True

    def test_create_client_local(self, tmp_path):
        """Local client should be PersistentClient."""
        client = create_chroma_client(persist_path=str(tmp_path / "chroma"))
        assert client is not None

    def test_create_client_cloud(self):
        """Cloud client should be ephemeral."""
        with patch("src.vector_store.is_streamlit_cloud", return_value=True):
            client = create_chroma_client()
            assert client is not None


class TestDocIdGeneration:
    """Tests for deterministic document ID creation."""

    def test_analysis_id(self):
        doc_id = _make_doc_id("analysis", "my-app", "20260213T143000")
        assert doc_id == "analysis-my-app-20260213T143000"

    def test_report_section_id(self):
        doc_id = _make_doc_id("report", "my-app", "20260213T143000", "build_health")
        assert doc_id == "report-build_health-my-app-20260213T143000"

    def test_no_section(self):
        doc_id = _make_doc_id("analysis", "proj", "ts")
        assert doc_id == "analysis-proj-ts"


class TestDevFlowVectorStore:
    """Tests for the DevFlowVectorStore class."""

    def test_initial_count_is_zero(self, vector_store):
        assert vector_store.count == 0

    def test_store_analysis(self, vector_store, sample_analysis):
        doc_id = vector_store.store_analysis(
            sample_analysis, project_name="test-project", model_used="gpt-4o-mini"
        )
        assert doc_id.startswith("analysis-test-project-")
        assert vector_store.count == 1

    def test_store_multiple_analyses(self, vector_store, sample_analysis):
        id1 = vector_store.store_analysis(sample_analysis, project_name="proj-a")
        id2 = vector_store.store_analysis(sample_analysis, project_name="proj-b")
        assert id1 != id2
        assert vector_store.count == 2

    def test_store_report_section(self, vector_store):
        doc_id = vector_store.store_report_section(
            section_name="build_health",
            content="Build health is good overall with 82% success rate.",
            project_name="test-project",
        )
        assert "report" in doc_id
        assert "build_health" in doc_id
        assert vector_store.count == 1

    def test_search_similar(self, vector_store, sample_analysis):
        vector_store.store_analysis(sample_analysis, project_name="test-project")
        results = vector_store.search_similar("high failure rate projects")
        assert len(results) >= 1
        assert "content" in results[0]
        assert "metadata" in results[0]
        assert results[0]["metadata"]["doc_type"] == "analysis"

    def test_search_similar_empty_store(self, vector_store):
        results = vector_store.search_similar("anything")
        assert results == []

    def test_search_by_project(self, vector_store, sample_analysis):
        vector_store.store_analysis(sample_analysis, project_name="alpha")
        vector_store.store_analysis(sample_analysis, project_name="beta")
        results = vector_store.search_by_project("alpha")
        assert len(results) >= 1
        assert all(r["metadata"]["project"] == "alpha" for r in results)

    def test_get_history(self, vector_store, sample_analysis):
        vector_store.store_analysis(sample_analysis, project_name="proj-a")
        vector_store.store_analysis(sample_analysis, project_name="proj-b")
        history = vector_store.get_history()
        assert len(history) == 2
        assert all("id" in entry for entry in history)
        assert all("metadata" in entry for entry in history)

    def test_get_history_empty(self, vector_store):
        history = vector_store.get_history()
        assert history == []

    def test_metadata_fields(self, vector_store, sample_analysis):
        vector_store.store_analysis(
            sample_analysis,
            project_name="test-project",
            model_used="gpt-4o-mini",
            temperature=0.5,
        )
        history = vector_store.get_history()
        meta = history[0]["metadata"]
        assert meta["project"] == "test-project"
        assert meta["doc_type"] == "analysis"
        assert meta["n_builds"] == 500
        assert meta["success_rate"] == 0.82
        assert meta["model_used"] == "gpt-4o-mini"
        assert meta["temperature"] == 0.5
