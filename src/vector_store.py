"""Vector store for historical CI/CD analysis persistence using ChromaDB."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import chromadb
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from .models import BuildAnalysisResult


def is_streamlit_cloud() -> bool:
    """Detect if running on Streamlit Cloud."""
    return (
        os.getenv("STREAMLIT_SHARING_MODE") is not None
        or os.path.exists("/mount/src")
    )


def create_chroma_client(
    persist_path: Optional[str] = None,
) -> chromadb.ClientAPI:
    """Create ChromaDB client appropriate for the environment.

    Uses PersistentClient for local development (data survives restarts)
    and ephemeral Client for Streamlit Cloud (no persistent filesystem).
    """
    if is_streamlit_cloud():
        return chromadb.Client()

    if persist_path is None:
        persist_path = str(Path(__file__).parent.parent / "data" / "chroma")

    os.makedirs(persist_path, exist_ok=True)
    return chromadb.PersistentClient(path=persist_path)


def _make_doc_id(
    doc_type: str, project: str, timestamp: str, section: str = ""
) -> str:
    """Create a deterministic document ID for idempotent upserts."""
    parts = [doc_type]
    if section:
        parts.append(section)
    parts.extend([project, timestamp])
    return "-".join(parts)


class DevFlowVectorStore:
    """ChromaDB-backed vector store for CI/CD analysis history.

    Stores BuildAnalysisResult documents as embeddings using OpenAI
    text-embedding-3-small. Supports similarity search and metadata filtering.
    """

    COLLECTION_NAME = "build_analyses"

    def __init__(
        self,
        client: Optional[chromadb.ClientAPI] = None,
        persist_path: Optional[str] = None,
    ):
        self._client = client or create_chroma_client(persist_path)
        self._embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self._vectorstore = Chroma(
            client=self._client,
            collection_name=self.COLLECTION_NAME,
            embedding_function=self._embeddings,
        )

    @property
    def count(self) -> int:
        """Number of documents in the collection."""
        collection = self._client.get_or_create_collection(self.COLLECTION_NAME)
        return collection.count()

    def store_analysis(
        self,
        analysis: BuildAnalysisResult,
        project_name: str = "multi-project",
        model_used: str = "unknown",
        temperature: float = 0.3,
    ) -> str:
        """Embed and store a BuildAnalysisResult.

        Returns the document ID.
        """
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        doc_id = _make_doc_id("analysis", project_name, timestamp)
        text = analysis.to_llm_context()

        metadata = {
            "doc_type": "analysis",
            "project": project_name,
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "n_builds": analysis.n_builds,
            "n_projects": analysis.n_projects,
            "success_rate": analysis.overall_success_rate,
            "failure_rate": analysis.overall_failure_rate,
            "median_duration_s": analysis.median_duration_seconds,
            "model_used": model_used,
            "temperature": temperature,
        }

        self._vectorstore.add_texts(
            texts=[text],
            metadatas=[metadata],
            ids=[doc_id],
        )
        return doc_id

    def store_report_section(
        self,
        section_name: str,
        content: str,
        project_name: str = "multi-project",
        model_used: str = "unknown",
    ) -> str:
        """Embed and store a report section (e.g., build_health, recommendations).

        Returns the document ID.
        """
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        doc_id = _make_doc_id("report", project_name, timestamp, section_name)

        metadata = {
            "doc_type": "report_section",
            "section": section_name,
            "project": project_name,
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "model_used": model_used,
        }

        self._vectorstore.add_texts(
            texts=[content],
            metadatas=[metadata],
            ids=[doc_id],
        )
        return doc_id

    def search_similar(
        self,
        query: str,
        k: int = 5,
        filter: Optional[dict] = None,
    ) -> list[dict]:
        """Search for similar documents by natural language query.

        Returns list of dicts with 'content', 'metadata', and 'score' keys.
        """
        if filter is None:
            filter = {"doc_type": "analysis"}

        results = self._vectorstore.similarity_search_with_relevance_scores(
            query, k=k, filter=filter
        )

        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score,
            }
            for doc, score in results
        ]

    def search_by_project(self, project: str, k: int = 5) -> list[dict]:
        """Search analyses for a specific project."""
        return self.search_similar(
            query=f"CI/CD analysis for {project}",
            k=k,
            filter={
                "$and": [
                    {"doc_type": "analysis"},
                    {"project": project},
                ]
            },
        )

    def get_history(self, limit: int = 20) -> list[dict]:
        """List recent analyses by date (most recent first).

        Returns metadata-only list (no embeddings or content).
        """
        collection = self._client.get_or_create_collection(self.COLLECTION_NAME)
        if collection.count() == 0:
            return []

        results = collection.get(
            where={"doc_type": "analysis"},
            limit=limit,
            include=["metadatas", "documents"],
        )

        entries = []
        for i, doc_id in enumerate(results["ids"]):
            entries.append(
                {
                    "id": doc_id,
                    "content": results["documents"][i] if results["documents"] else "",
                    "metadata": results["metadatas"][i] if results["metadatas"] else {},
                }
            )

        # Sort by analysis_date descending
        entries.sort(
            key=lambda e: e["metadata"].get("analysis_date", ""),
            reverse=True,
        )
        return entries
