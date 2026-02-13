# Sprint A: Vector DB — Historical Analysis Persistence

**Sprint Goal:** Add ChromaDB persistence so the agent can store and retrieve historical CI/CD analyses across sessions.

**Duration:** 3 days

**Prerequisites:** Epoch 1 complete

**Research:** [docs/research/chromadb_vector_store.md](../research/chromadb_vector_store.md)

---

## Sprint Backlog

### Day 1: ChromaDB Setup + Embedding Pipeline

**Objective:** Install ChromaDB, create the vector store wrapper, and implement the embedding pipeline.

**Tasks:**
- [ ] Add `chromadb>=0.5.0` and `langchain-chroma>=0.2.0` to `requirements.txt`
- [ ] Create `src/vector_store.py`:
  - `is_streamlit_cloud()` — detect environment via `/mount/src`
  - `create_chroma_client()` — PersistentClient locally, Client() on cloud
  - `DevFlowVectorStore` class:
    - `__init__(self, collection_name="build_analyses")`
    - Uses `OpenAIEmbeddings(model="text-embedding-3-small")`
    - Creates `langchain_chroma.Chroma` vectorstore instance
    - `store_analysis(self, analysis: BuildAnalysisResult, metadata: dict)` — embed and upsert
    - `store_report_section(self, section_name, content, metadata)` — embed report sections
    - `_make_doc_id(doc_type, project, timestamp, section)` — deterministic IDs
- [ ] Add `data/chroma/` to `.gitignore`
- [ ] Write `tests/test_vector_store.py`:
  - Test client creation (local vs cloud detection)
  - Test store_analysis with mock data
  - Test deterministic ID generation

**Deliverables:**
- `src/vector_store.py`
- `tests/test_vector_store.py`
- Updated `requirements.txt`, `.gitignore`

**Acceptance Criteria:**
- [ ] ChromaDB installs without errors
- [ ] Vector store creates/opens collection successfully
- [ ] Can store a BuildAnalysisResult and retrieve it by ID
- [ ] Tests pass

---

### Day 2: Retrieval Chain + Agent Tool

**Objective:** Create the retrieval tool and integrate it with the existing agent.

**Tasks:**
- [ ] Add retrieval methods to `DevFlowVectorStore`:
  - `search_similar(self, query: str, k=5, filter=None)` — similarity search
  - `search_by_project(self, project: str, k=5)` — project-filtered search
  - `get_history(self, limit=20)` — list recent analyses by date
- [ ] Create `search_historical_analyses` tool in `src/agent.py`:
  - `@tool` decorated function
  - Accepts natural language query
  - Returns formatted historical analysis excerpts with metadata
  - Graceful fallback: "No historical data available" when vector store is empty
- [ ] Add `search_historical_analyses` to agent's tool list (5th tool)
- [ ] Wire vector store into `DevFlowAgent`:
  - Accept optional `vector_store` parameter in constructor
  - Auto-store analysis results after each `analyze()` call
- [ ] Write tests:
  - Test retrieval with mock embedded data
  - Test agent tool integration
  - Test graceful fallback when no history exists

**Deliverables:**
- Updated `src/vector_store.py` (retrieval methods)
- Updated `src/agent.py` (new tool + vector store integration)
- `tests/test_retrieval.py`

**Acceptance Criteria:**
- [ ] Agent can answer "Have we seen this before?" type questions
- [ ] Similarity search returns relevant past analyses
- [ ] Empty vector store handled gracefully
- [ ] Tests pass

---

### Day 3: UI Integration + Testing

**Objective:** Add history section to Streamlit UI and end-to-end testing.

**Tasks:**
- [ ] Add "History" section to Streamlit app:
  - Sidebar toggle: "Enable Historical Analysis" (initializes vector store)
  - History tab or expandable section showing past analyses
  - Semantic search input: "Find similar past analyses"
  - Auto-save toggle: store analysis results after each run
- [ ] Wire vector store into `app.py` session state:
  - `st.session_state.vector_store` — initialized once per session
  - Pass vector store to `DevFlowAgent` constructor
- [ ] Integration testing:
  - Upload CSV → analyze → store → search → retrieve
  - Verify persistence across page refreshes (local only)
  - Verify graceful degradation on Streamlit Cloud (in-memory mode)
- [ ] Update README with Sprint A features

**Deliverables:**
- Updated `app.py` (history UI)
- Integration test script
- Updated README

**Acceptance Criteria:**
- [ ] Can store analysis, close app, reopen, and find previous analysis (local)
- [ ] History search returns relevant results
- [ ] Streamlit Cloud deployment still works (in-memory mode)
- [ ] All tests pass

---

## Dependencies Added

| Package | Version | Purpose |
|---------|---------|---------|
| `chromadb` | >=0.5.0 | Vector database |
| `langchain-chroma` | >=0.2.0 | LangChain integration |

Already installed: `openai==2.15.0`, `langchain-openai==1.1.7` (includes `OpenAIEmbeddings`).

---

## Key Architecture Decisions

| Decision | Choice | Reference |
|----------|--------|-----------|
| Embedding model | text-embedding-3-small (1536d) | Research doc §2 |
| Persistence | PersistentClient locally, Client() on cloud | Research doc §3 |
| Collection count | 1 (`build_analyses`) with doc_type metadata | Research doc §4 |
| Document IDs | Deterministic `{type}-{project}-{timestamp}` | Research doc §4 |
| Retrieval | Similarity search (MMR deferred) | Research doc §5 |

---

## Risks

| Risk | Mitigation |
|------|------------|
| ChromaDB version incompatibility | Pin to >=0.5.0, test install before coding |
| Streamlit Cloud memory limits | In-memory mode, small collection size |
| Embedding cost | text-embedding-3-small is $0.02/1M tokens; negligible |
