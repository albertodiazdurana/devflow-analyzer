# Research: Epoch 2 — Advanced Agent Architecture

**Purpose/Question:** What features would maximize DevFlow Analyzer's portfolio value for Senior ML Engineer / AI Engineer roles?
**Target Outcome:** Validated sprint plan for Epoch 2 implementation
**Status:** Active
**Date Created:** 2026-02-13
**Date Completed:**
**Outcome Reference:**

---

## Epoch 1 Recap (Days 1-6, Complete)

| Day | Deliverable | Lines |
|-----|------------|-------|
| 1 | Process analyzer, data models, DFG visualization | ~400 |
| 2 | LLM provider factory, prompt templates, report generation | ~500 |
| 3 | ReAct agent with LangGraph, 4 tools | ~230 |
| 4 | MLflow evaluation, ROUGE scoring, cost tracking | ~300 |
| 5 | Streamlit app (4 tabs), deployment to cloud | ~900 |
| 6 | A/B testing, user evaluation, experiment tracking | ~280 |

**Current architecture:** Single ReAct agent, session-based state (no persistence), monolith Streamlit app, OpenAI models only.

---

## Proposed Epoch 2 Features

### Feature 1: Multi-Agent Orchestration

**What:** Add a second specialized agent ("Root Cause Analyzer") that collaborates with the existing "Investigator" agent via a LangGraph supervisor pattern.

**Why (portfolio value):**
- Multi-agent is the #1 skill gap in the portfolio (SQL Query Agent and DevFlow are both single-agent)
- BMW Agentic AI Engineer, Delivery Hero, Scalable Capital all explicitly require multi-agent experience
- Demonstrates LangGraph beyond `create_react_agent`

**Scope:**
- New agent: Root Cause Analyzer with specialized tools (temporal analysis, correlation detection)
- Supervisor graph: Routes questions to appropriate agent or orchestrates both
- Shared context: Both agents access the same BuildAnalysisResult
- UI: Agent tab shows which agent(s) responded, routing decision

**New files:**
- `src/agents/investigator.py` — Existing agent refactored
- `src/agents/root_cause.py` — New specialized agent
- `src/agents/supervisor.py` — LangGraph supervisor graph
- `tests/test_agents.py` — Tests for multi-agent orchestration

**Depends on:** Nothing (can start independently)

**Effort estimate:** 3-4 days
- Day 1: Research LangGraph supervisor patterns, design agent graph
- Day 2: Implement Root Cause Analyzer agent with new tools
- Day 3: Build supervisor graph, integrate with existing pipeline
- Day 4: UI integration, testing, documentation

---

### Feature 2: Vector DB for Historical Analysis

**What:** Store past analyses and agent responses in ChromaDB, enabling RAG-style retrieval ("show me similar failures from previous analyses").

**Why (portfolio value):**
- 5-6 of 8 target job openings require vector database experience
- Adds persistence (currently session-only — data lost on refresh)
- Demonstrates embeddings, retrieval, and semantic search
- Enables cross-session comparison ("how did failure rates change?")

**Scope:**
- ChromaDB local storage for analysis results and agent responses
- Embedding pipeline: OpenAI text-embedding-3-small for analysis chunks
- Retrieval tool: Agent can query historical analyses
- UI: "History" section showing past sessions, semantic search

**New files:**
- `src/vector_store.py` — ChromaDB wrapper, embedding pipeline
- `src/retrieval.py` — Retrieval chain for historical queries
- `tests/test_vector_store.py` — Tests
- `data/chroma/` — Local ChromaDB storage

**Depends on:** Nothing (can start independently, but enhances Multi-Agent if done first)

**Effort estimate:** 2-3 days
- Day 1: ChromaDB setup, embedding pipeline, storage schema
- Day 2: Retrieval chain, agent tool integration
- Day 3: UI integration, persistence across sessions, testing

---

### Feature 3: REST API Backend

**What:** FastAPI wrapper exposing the analysis pipeline as a REST API, decoupled from Streamlit.

**Why (portfolio value):**
- Zalando, Delivery Hero, intive all require API design experience
- Demonstrates clean separation of concerns (API vs UI)
- Makes the tool usable programmatically (CI/CD integration, webhooks)
- Low effort, high signal

**Scope:**
- FastAPI app with endpoints: upload data, run analysis, query agent, get history
- Pydantic models for request/response validation
- OpenAPI docs auto-generated
- Docker-ready (Dockerfile for API)

**New files:**
- `api.py` — FastAPI application
- `src/api_models.py` — Pydantic request/response schemas
- `tests/test_api.py` — API endpoint tests
- `Dockerfile` — Container for API deployment

**Depends on:** Nothing

**Effort estimate:** 2-3 days
- Day 1: FastAPI setup, core endpoints (upload, analyze, agent query)
- Day 2: Response models, error handling, OpenAPI docs
- Day 3: Docker, integration tests, documentation

---

## Effort Summary

| Feature | Days | New Files | Complexity | Portfolio Signal |
|---------|------|-----------|------------|-----------------|
| Multi-Agent Orchestration | 3-4 | 4 | High | Very High |
| Vector DB Historical Analysis | 2-3 | 3 | Medium | High |
| REST API Backend | 2-3 | 4 | Low-Medium | High |
| **Total** | **7-10** | **11** | | |

## Proposed Sprint Structure

### Sprint A: Foundation + Vector DB (3 days)
- Set up ChromaDB persistence layer
- Build embedding pipeline and retrieval chain
- Add history retrieval tool to existing agent
- **Deliverable:** Agent can search past analyses

### Sprint B: Multi-Agent (4 days)
- Refactor agent.py into agents/ package
- Implement Root Cause Analyzer with temporal/correlation tools
- Build LangGraph supervisor graph
- Integrate with Streamlit UI
- **Deliverable:** Two-agent system with routing

### Sprint C: API + Docker (3 days)
- FastAPI backend wrapping analysis pipeline
- Pydantic models, OpenAPI documentation
- Dockerfile for containerized deployment
- **Deliverable:** REST API + Docker image

## Dependency Graph

```
Vector DB (Sprint A)
    │
    ├──> Multi-Agent (Sprint B) — agents can query history
    │
REST API (Sprint C) — wraps everything, independent
```

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| LangGraph supervisor complexity | Multi-agent may take longer than estimated | Start with simple router, upgrade to full supervisor |
| ChromaDB persistence in Streamlit Cloud | Cloud may not support local file storage | Use in-memory for cloud, persistent for local/Docker |
| Scope creep | Each feature could expand significantly | Strict MVP per sprint, backlog extras |

## Next Steps (if approved)

1. **Research phase:** Study LangGraph multi-agent patterns, ChromaDB best practices, FastAPI + LangChain integration
2. **Document findings** in `docs/research/`
3. **Create sprint plans** in `docs/plans/`
4. **Implement** Sprint A → B → C
