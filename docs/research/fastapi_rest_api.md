# Research: FastAPI REST API Integration

**Purpose/Question:** How to wrap the DevFlow Analyzer pipeline as a REST API with FastAPI?
**Target Outcome:** Architecture and implementation plan for Sprint C (REST API + Docker)
**Status:** Complete
**Date Created:** 2026-02-13

---

## 1. Integration Approach

### LangServe: Do Not Use

LangServe (v0.3.3) is in maintenance mode. It was designed for simple `Runnable` chains, not LangGraph agents. The LangChain team shifted focus to LangGraph Platform for deployment.

**Decision:** Direct FastAPI wrapping. More flexible, works with LangGraph agents, demonstrates engineering depth.

### Async Support

LangGraph agents support `ainvoke` natively. Use `async def` endpoints with `await agent.ainvoke()`:

```python
result = await self.agent.ainvoke({"messages": [("user", task)]})
```

Existing `@tool`-decorated functions are synchronous -- LangGraph runs them in a thread pool executor when called from async context. No changes needed to tool functions.

### Lifespan Pattern

FastAPI deprecated `@app.on_event("startup")` in favor of `lifespan` context manager (since 0.109.0):

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: validate environment
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY required")
    yield
    # Shutdown: cleanup

app = FastAPI(title="DevFlow Analyzer API", lifespan=lifespan)
```

---

## 2. API Endpoint Design

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/upload` | Upload CSV, returns `analysis_id` |
| `GET` | `/api/v1/analysis/{id}` | Get analysis results |
| `POST` | `/api/v1/analysis/{id}/report` | Generate LLM report |
| `POST` | `/api/v1/agent/query` | Ask agent a question (sync) |
| `POST` | `/api/v1/agent/stream` | Stream agent response (SSE) |
| `GET` | `/api/v1/history` | List past analyses |
| `DELETE` | `/api/v1/analysis/{id}` | Remove analysis |

### URL Path Versioning

Use `APIRouter(prefix="/api/v1")` for versioning. Single `v1` sufficient for MVP.

---

## 3. File Upload

```python
@app.post("/api/v1/upload", response_model=AnalysisResponse)
async def upload_and_analyze(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Only CSV files are supported")

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="wb") as tmp:
        content = await file.read()
        if len(content) > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(413, "File too large")
        tmp.write(content)
        tmp_path = tmp.name

    try:
        analyzer = ProcessAnalyzer(data_path=tmp_path)
        analyzer.load_data()
        result = analyzer.analyze()
        analysis_id = str(uuid.uuid4())
        analysis_store[analysis_id] = result
        return AnalysisResponse(analysis_id=analysis_id, summary=result.to_dict())
    finally:
        Path(tmp_path).unlink(missing_ok=True)
```

Requires `python-multipart>=0.0.18` (installed automatically with FastAPI 0.113+).

---

## 4. Streaming with SSE

```python
from sse_starlette.sse import EventSourceResponse

@app.post("/api/v1/agent/stream")
async def stream_agent_query(request: AgentQueryRequest):
    async def event_generator():
        async for event in agent.agent.astream_events(
            {"messages": [("user", request.question)]},
            version="v2",
        ):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield {"event": "token", "data": content}
            elif kind == "on_tool_start":
                yield {"event": "tool_call", "data": f"Calling: {event['name']}"}
            elif kind == "on_tool_end":
                yield {"event": "tool_result", "data": f"Result from: {event['name']}"}
        yield {"event": "done", "data": ""}

    return EventSourceResponse(event_generator())
```

Requires `sse-starlette>=2.0.0`.

---

## 5. Pydantic Models

Create `src/api_models.py` with Pydantic v2 schemas parallel to existing dataclasses. Convert via:

```python
AnalysisSummary(**analysis_result.to_dict())
```

Key models: `AnalysisResponse`, `AgentQueryRequest`, `AgentQueryResponse`, `HealthResponse`.

---

## 6. Long-Running Tasks

Three options, in order of complexity:

1. **Synchronous** (MVP): Direct `await` in endpoint. Set client timeout to 120s.
2. **SSE streaming** (best UX): Real-time token streaming via `astream_events`.
3. **Background + polling** (production): `BackgroundTasks` + task status endpoint.

**Recommendation:** Start with sync for `/agent/query`, add SSE for `/agent/stream`.

---

## 7. Docker Containerization

### Multi-Stage Build

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim AS runtime
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends graphviz libgraphviz-dev && rm -rf /var/lib/apt/lists/*
COPY --from=builder /install /usr/local
COPY src/ src/
COPY api.py .
RUN useradd -m appuser
USER appuser
EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

**PM4Py dependency:** Requires `graphviz` + `libgraphviz-dev` at runtime for DFG visualization. Skip if DFG not needed in API.

### Docker Compose

```yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    command: uvicorn api:app --host 0.0.0.0 --port 8000 --reload

  streamlit:
    build: {context: ., dockerfile: Dockerfile.streamlit}
    ports: ["8501:8501"]
    environment:
      - DEVFLOW_API_URL=http://api:8000
    depends_on: {api: {condition: service_healthy}}
```

---

## 8. Deployment Architecture

### Dual Mode (Sprint C)

```
Streamlit Cloud (app.py) ──imports──> src/   (unchanged)
Railway/Render (api.py)  ──imports──> src/   (new interface)
                                       │
                                  OpenAI API
```

`app.py` and `api.py` coexist. Both import `src/` directly. API is additive -- no changes to Streamlit deployment.

### Full Decoupling (Future/Epoch 3)

`app.py` uses `httpx` to call `api.py` instead of importing `src/`. Only one "brain" (the API). Streamlit becomes a pure UI layer.

---

## 9. Testing

### httpx + ASGITransport

```python
from httpx import AsyncClient, ASGITransport

async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
    response = await client.post("/api/v1/upload", files={"file": ("builds.csv", f, "text/csv")})
```

### Mock LLM for Agent Tests

Use `FakeListChatModel` or `unittest.mock.patch` to avoid OpenAI API calls in tests.

### Test Coverage

- Upload: valid CSV, invalid format, empty, oversized, missing columns
- Agent: sync query, streaming, invalid analysis_id
- Health: returns 200 with status

---

## 10. Dependencies for Sprint C

```
# API
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
python-multipart>=0.0.18
pydantic-settings>=2.0.0
sse-starlette>=2.0.0

# Testing
httpx>=0.27.0
pytest-asyncio>=0.24.0
```

---

## 11. Items to Verify Before Implementation

These may have changed after May 2025:

1. LangServe deprecation notice on GitHub
2. LangGraph Platform self-hosted options
3. LangGraph 1.0 migration guide (if upgrading from 0.x)
4. `astream_events` v2 event schema stability
5. Railway/Render current pricing

---

## 12. Architecture Decision Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Framework | FastAPI (not LangServe) | LangServe in maintenance, no LangGraph support |
| Async | `ainvoke` in async endpoints | Native support, no blocking |
| Streaming | SSE via sse-starlette | Simpler than WebSockets for request-response |
| File upload | `UploadFile` + temp file | ProcessAnalyzer expects file path |
| Models | Pydantic v2 parallel to dataclasses | API validation, auto docs |
| Versioning | URL path `/api/v1/` | Simple, explicit |
| Architecture | Dual mode (API + Streamlit coexist) | Additive, no risk to existing deployment |
| Docker | Multi-stage build, python:3.12-slim | Smaller image, no compiler in runtime |
| Deployment | Railway or Render for API | Docker-native, affordable |
