# Sprint C: REST API + Docker

**Sprint Goal:** Expose the analysis pipeline as a FastAPI REST API with Docker containerization.

**Duration:** 3 days

**Prerequisites:** Sprint A and B complete (vector store + multi-agent available via API)

**Research:** [docs/research/fastapi_rest_api.md](../research/fastapi_rest_api.md)

---

## Sprint Backlog

### Day 1: FastAPI Core Endpoints

**Objective:** Create the FastAPI application with core analysis and agent query endpoints.

**Tasks:**
- [ ] Add API dependencies to `requirements.txt`:
  - `fastapi>=0.115.0`, `uvicorn[standard]>=0.30.0`
  - `python-multipart>=0.0.18`, `pydantic-settings>=2.0.0`
  - `sse-starlette>=2.0.0`
- [ ] Create `src/api_models.py`:
  - `HealthResponse` — status, version, openai_configured
  - `AnalysisSummary` — Pydantic v2 mirror of BuildAnalysisResult.to_dict()
  - `AnalysisResponse` — analysis_id + summary
  - `AgentQueryRequest` — analysis_id, question, model_key
  - `AgentQueryResponse` — question, response, model_key, latency_ms
- [ ] Create `api.py` (project root):
  - Lifespan context manager (validate OPENAI_API_KEY)
  - In-memory `analysis_store: dict[str, BuildAnalysisResult]`
  - `GET /health` — health check
  - `POST /api/v1/upload` — CSV upload via UploadFile, run ProcessAnalyzer, return analysis_id
  - `GET /api/v1/analysis/{id}` — retrieve stored analysis
  - `POST /api/v1/agent/query` — sync agent query via ainvoke
  - `DELETE /api/v1/analysis/{id}` — remove analysis
  - URL versioning via `APIRouter(prefix="/api/v1")`
- [ ] Write `tests/test_api.py`:
  - Health endpoint returns 200
  - Upload valid CSV returns analysis_id
  - Upload invalid file returns 400
  - Agent query returns response
  - Agent query with invalid analysis_id returns 404

**Deliverables:**
- `src/api_models.py`
- `api.py`
- `tests/test_api.py`
- Updated `requirements.txt`

**Acceptance Criteria:**
- [ ] `uvicorn api:app` starts without errors
- [ ] Swagger docs at `/docs` show all endpoints
- [ ] Upload → query cycle works end-to-end
- [ ] Tests pass

---

### Day 2: Streaming + History Endpoints

**Objective:** Add SSE streaming for agent responses and history endpoints.

**Tasks:**
- [ ] Add SSE streaming endpoint to `api.py`:
  - `POST /api/v1/agent/stream` — EventSourceResponse with astream_events(v2)
  - Events: `token` (LLM output), `tool_call` (tool start), `tool_result` (tool end), `done`
- [ ] Add history endpoints:
  - `GET /api/v1/history` — list past analyses (from vector store)
  - `POST /api/v1/analysis/{id}/report` — generate LLM report for stored analysis
- [ ] Add structured logging middleware:
  - Log request method, path, status code, duration_ms
- [ ] Add CORS middleware (allow Streamlit frontend origin)
- [ ] Add pydantic-settings `Settings` class:
  - `openai_api_key`, `log_level`, `max_upload_size_mb`, `allowed_origins`
  - Load from `.env` file
- [ ] Write tests:
  - SSE streaming returns event stream
  - History endpoint returns stored analyses
  - CORS headers present

**Deliverables:**
- Updated `api.py` (streaming + history + middleware)
- `tests/test_api_streaming.py`

**Acceptance Criteria:**
- [ ] SSE stream delivers tokens in real-time
- [ ] History endpoint returns past analyses
- [ ] Logging shows request/response metrics
- [ ] Tests pass

---

### Day 3: Docker + Documentation

**Objective:** Containerize the API and complete documentation.

**Tasks:**
- [ ] Create `Dockerfile`:
  - Multi-stage build (builder + runtime)
  - `python:3.12-slim` base
  - Install graphviz for PM4Py in runtime stage
  - Non-root user (`appuser`)
  - Health check via httpx
  - `CMD uvicorn api:app --host 0.0.0.0 --port 8000`
- [ ] Create `docker-compose.yml`:
  - `api` service: build from Dockerfile, port 8000, env vars from `.env`
  - `streamlit` service: port 8501, depends on api health
  - Development mode with volume mounts and `--reload`
- [ ] Create `.dockerignore`:
  - Exclude `.venv/`, `data/`, `.git/`, `__pycache__/`, `.env`, `*.pyc`
- [ ] Test Docker build and run:
  - `docker build -t devflow-api .`
  - `docker run -e OPENAI_API_KEY=... -p 8000:8000 devflow-api`
  - Verify health endpoint, upload, agent query
- [ ] Update README with Sprint C features:
  - API usage examples (curl commands)
  - Docker setup instructions
  - Endpoint documentation
- [ ] Move `docs/plans/SPRINT_C.md` to `docs/plans/done/`

**Deliverables:**
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- Updated README

**Acceptance Criteria:**
- [ ] Docker image builds successfully
- [ ] Container starts and serves API on port 8000
- [ ] All endpoints work inside container
- [ ] `docker-compose up` starts both API and Streamlit
- [ ] README documents API usage

---

## API Endpoint Summary

| Method | Endpoint | Purpose | Day |
|--------|----------|---------|-----|
| `GET` | `/health` | Health check | 1 |
| `POST` | `/api/v1/upload` | Upload CSV | 1 |
| `GET` | `/api/v1/analysis/{id}` | Get analysis | 1 |
| `POST` | `/api/v1/agent/query` | Agent query (sync) | 1 |
| `DELETE` | `/api/v1/analysis/{id}` | Remove analysis | 1 |
| `POST` | `/api/v1/agent/stream` | Agent query (SSE) | 2 |
| `GET` | `/api/v1/history` | List past analyses | 2 |
| `POST` | `/api/v1/analysis/{id}/report` | Generate report | 2 |

---

## Dependencies Added

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | >=0.115.0 | Web framework |
| `uvicorn[standard]` | >=0.30.0 | ASGI server |
| `python-multipart` | >=0.0.18 | File upload support |
| `pydantic-settings` | >=2.0.0 | Settings from env vars |
| `sse-starlette` | >=2.0.0 | Server-Sent Events |
| `httpx` | >=0.27.0 | Testing + health check |
| `pytest-asyncio` | >=0.24.0 | Async test support |

---

## Architecture: Dual Mode

```
Streamlit Cloud (app.py) ──imports──> src/   (unchanged)
Docker (api.py)          ──imports──> src/   (new interface)
                                       │
                                  OpenAI API
```

Both interfaces coexist. The API is additive -- no changes to existing Streamlit deployment.

---

## Risks

| Risk | Mitigation |
|------|------------|
| PM4Py Docker deps | Multi-stage build, graphviz in runtime only |
| Agent timeout (>30s) | Sync endpoint with 120s timeout; SSE for real-time feedback |
| Image size (>1GB) | Multi-stage build, slim base, no compiler in runtime |
| Cloud deployment cost | Railway/Render hobby tier ($5-7/mo); defer until needed |
