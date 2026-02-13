# Research: ChromaDB Vector Store for Historical Analysis Persistence

**Purpose/Question:** How to integrate ChromaDB with OpenAI embeddings for storing and retrieving historical CI/CD analyses?
**Target Outcome:** Architecture and implementation plan for Sprint A (Vector DB)
**Status:** Complete
**Date Created:** 2026-02-13

---

## 1. ChromaDB Setup and Configuration

### Package Installation

```
chromadb>=0.5.0
langchain-chroma>=0.2.0
```

The `langchain-chroma` dedicated package supersedes the deprecated `langchain-community` Chroma wrapper.

### Client Modes

```python
import chromadb

# Ephemeral (in-memory) - data lost on process exit
client = chromadb.Client()

# Persistent (local disk) - data survives restarts
client = chromadb.PersistentClient(path="./data/chroma")
```

For DevFlow Analyzer:
- **Local development:** `PersistentClient(path="./data/chroma")`
- **Streamlit Cloud:** `Client()` (ephemeral filesystem, data lost on restart)

### Cloud Detection

```python
import os

def is_streamlit_cloud() -> bool:
    return (
        os.getenv("STREAMLIT_SHARING_MODE") is not None
        or os.path.exists("/mount/src")  # Streamlit Cloud mounts repo here
    )
```

### Collection Management

```python
collection = client.get_or_create_collection(
    name="build_analyses",
    metadata={"hnsw:space": "cosine"},
    embedding_function=embedding_fn
)
```

### Metadata Filtering

Supports `$lt`, `$gte`, `$ne`, `$in`, `$and`, `$or` operators. Values must be scalar (str, int, float, bool) -- no lists or nested dicts.

```python
results = collection.query(
    query_texts=["slow build analysis"],
    n_results=5,
    where={
        "$and": [
            {"project": "my-app"},
            {"success_rate": {"$lt": 0.8}}
        ]
    }
)
```

---

## 2. OpenAI Embeddings Integration

### Model: text-embedding-3-small

| Dimensions | MTEB Score | Storage/Vector | Cost per 1M tokens |
|-----------|-----------|---------------|---------------------|
| 1536 (default) | ~62.3% | 6 KB | $0.020 |
| 512 | ~61.0% | 2 KB | $0.020 |

**Recommendation:** 1536 (default). Low volume (analyses are 300-500 tokens each), storage is not a constraint. Embedding 1,000 analyses costs ~$0.01.

### ChromaDB Integration

```python
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

embedding_fn = OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-3-small"
)
```

Or via LangChain:

```python
from langchain_openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
```

### Batch Embedding

The API supports up to 2048 inputs per batch, max 8191 tokens per input. Each `to_llm_context()` output is 300-500 tokens -- no chunking needed.

---

## 3. Schema Design

### Single Collection Strategy

One collection (`build_analyses`) with `doc_type` metadata discriminator. Low volume makes partitioning unnecessary.

### What to Embed

1. **Analysis document:** Full `BuildAnalysisResult.to_llm_context()` output (quantitative patterns)
2. **Report documents:** LLM-generated narrative sections from `CICDReport` (qualitative insights)

### Metadata Fields

```python
metadata = {
    "project": "my-app",              # or "multi-project"
    "analysis_date": "2026-02-13",    # ISO date string
    "doc_type": "analysis",           # "analysis" | "report_section"
    "section": "build_health",        # only for report sections
    "n_builds": 1500,
    "n_projects": 12,
    "success_rate": 0.847,
    "failure_rate": 0.102,
    "median_duration_s": 245.0,
    "model_used": "gpt-4o-mini",
    "temperature": 0.3,
    "agent_task": "full_analysis",
}
```

### Document ID Strategy

Deterministic IDs for idempotent upserts:

```python
def make_doc_id(doc_type: str, project: str, timestamp: str, section: str = "") -> str:
    parts = [doc_type]
    if section:
        parts.append(section)
    parts.extend([project, timestamp])
    return "-".join(parts)
```

---

## 4. Retrieval Patterns

### Similarity Search (Initial)

```python
from langchain_chroma import Chroma

vectorstore = Chroma(
    client=chroma_client,
    collection_name="build_analyses",
    embedding_function=embeddings,
)

docs = vectorstore.similarity_search(
    "projects with high failure rates",
    k=5,
    filter={"doc_type": "analysis"}
)
```

### MMR (Future, When Volume Grows)

```python
docs = vectorstore.max_marginal_relevance_search(
    "projects with high failure rates",
    k=5, fetch_k=20, lambda_mult=0.7,
    filter={"doc_type": "analysis"}
)
```

### Agent Tool Integration

New `search_historical_analyses` tool for the LangGraph agent:

```python
@tool
def search_historical_analyses(query: str) -> str:
    """Search historical CI/CD analyses for relevant past results."""
    if _vectorstore is None:
        return "No historical data available."

    docs = _vectorstore.similarity_search(query, k=3, filter={"doc_type": "analysis"})
    if not docs:
        return "No relevant historical analyses found."

    results = []
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata
        results.append(
            f"### Historical Analysis {i}\n"
            f"**Project:** {meta.get('project', 'unknown')} | "
            f"**Date:** {meta.get('analysis_date', 'unknown')} | "
            f"**Success Rate:** {meta.get('success_rate', 'N/A')}\n\n"
            f"{doc.page_content}\n"
        )
    return "\n---\n".join(results)
```

---

## 5. Persistence Strategy Summary

| Environment | Client | Persistence | Detection |
|-------------|--------|------------|-----------|
| Local dev | `PersistentClient("./data/chroma")` | Disk (SQLite + binaries) | Default |
| Streamlit Cloud | `Client()` | In-memory only | `/mount/src` exists |
| Docker (future) | `PersistentClient` or `HttpClient` | Volume mount or Chroma server | Env var |

Add `data/chroma/` to `.gitignore`.

---

## 6. Key Dependencies

```
chromadb>=0.5.0
langchain-chroma>=0.2.0
```

Already installed: `openai==2.15.0`, `langchain-openai==1.1.7` (includes `OpenAIEmbeddings`).

---

## 7. Architecture Decision Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Embedding model | text-embedding-3-small (1536d) | Cost-effective, sufficient quality |
| Persistence | PersistentClient locally, Client() on cloud | Matches Streamlit Cloud constraints |
| Collection count | 1 (`build_analyses`) | Low volume, doc_type for filtering |
| What to embed | Full to_llm_context() + report sections | Under token limit, no chunking |
| Document IDs | Deterministic `{type}-{project}-{timestamp}` | Idempotent upserts |
| LangChain integration | `langchain-chroma` package | Recommended over community package |
| Retrieval | Similarity search initially, MMR later | Simplicity first |
| Agent integration | New `search_historical_analyses` tool | Fits existing ReAct pattern |
