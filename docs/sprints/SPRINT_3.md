# Sprint 3: Integrations & API

**Sprint Goal:** Enable programmatic access and direct CI/CD system integrations so DevFlow Analyzer can receive data automatically.

**Duration:** 5 days

**Backlog Items:** B-007, B-008, B-009

**Prerequisites:** Sprint 1 & 2 completed

---

## Sprint Backlog

### Day 1-2: REST API Endpoint (B-007)

**Objective:** Create a REST API for CI/CD systems to push build data and receive automated reports.

#### Day 1: API Design & Implementation

**Tasks:**
- [ ] Create `api/` directory structure
- [ ] Implement FastAPI application in `api/main.py`
- [ ] Design API endpoints:
  ```
  POST /api/v1/builds        - Submit build data
  GET  /api/v1/analysis      - Get analysis results
  POST /api/v1/analyze       - Trigger analysis on submitted data
  GET  /api/v1/health        - Health check
  ```
- [ ] Create API data models (Pydantic schemas)
- [ ] Add API key authentication (simple Bearer token)
- [ ] Write basic tests

**Deliverables:**
- `api/main.py` - FastAPI app
- `api/schemas.py` - Request/response models
- `api/auth.py` - API key validation
- `tests/test_api.py`

**Acceptance Criteria:**
- [ ] Can POST build data via API
- [ ] Returns analysis results as JSON
- [ ] API key required for access
- [ ] Health check endpoint works

#### Day 2: API Deployment & Documentation

**Tasks:**
- [ ] Add API documentation (OpenAPI/Swagger auto-generated)
- [ ] Configure for deployment (separate from Streamlit or integrated)
- [ ] Add rate limiting
- [ ] Create example curl commands
- [ ] Write API usage guide in `docs/api.md`

**Deliverables:**
- API documentation page
- `docs/api.md` usage guide
- Deployment configuration

**Acceptance Criteria:**
- [ ] Swagger UI accessible at `/docs`
- [ ] Example requests documented
- [ ] Rate limiting prevents abuse
- [ ] Works when deployed

---

### Day 3-4: GitHub Actions Integration (B-008)

**Objective:** Fetch build data directly from GitHub Actions without manual CSV upload.

#### Day 3: GitHub API Integration

**Tasks:**
- [ ] Create `src/integrations/github.py`
- [ ] Implement GitHub Actions API client:
  - List workflow runs for a repository
  - Get run details (status, duration, timestamp)
  - Handle pagination for large repos
- [ ] Map GitHub Actions data to TravisTorrent schema
- [ ] Add GitHub token configuration
- [ ] Write tests with mocked responses

**Deliverables:**
- `src/integrations/github.py`
- `tests/test_github_integration.py`
- Token configuration in `.env.example`

**Acceptance Criteria:**
- [ ] Can fetch workflow runs from public repos
- [ ] Handles private repos with token
- [ ] Maps to expected data format
- [ ] Tests pass with mocked API

#### Day 4: GitHub Integration UI

**Tasks:**
- [ ] Add "Import from GitHub" option in Upload tab
- [ ] Create repository input (owner/repo format)
- [ ] Add branch/workflow filters
- [ ] Show import progress
- [ ] Handle errors (repo not found, rate limits)
- [ ] Add "Connect GitHub Account" flow (OAuth optional, or just token)

**Deliverables:**
- GitHub import UI in Upload tab
- Progress indicator
- Error handling

**Acceptance Criteria:**
- [ ] Can enter repo and fetch builds
- [ ] Shows progress during import
- [ ] Clear error messages for failures
- [ ] Imported data analyzed correctly

---

### Day 5: Webhook Support (B-009)

**Objective:** Receive real-time build events via webhooks from CI/CD systems.

**Tasks:**
- [ ] Add webhook endpoint to API:
  ```
  POST /api/v1/webhook/github   - GitHub Actions webhook
  POST /api/v1/webhook/generic  - Generic CI/CD webhook
  ```
- [ ] Implement webhook signature verification (GitHub HMAC)
- [ ] Create webhook event processor
- [ ] Store incoming events for analysis
- [ ] Add webhook setup instructions for GitHub
- [ ] Create webhook testing utility

**Deliverables:**
- Webhook endpoints in API
- Signature verification
- `docs/webhooks.md` setup guide
- Webhook test utility

**Acceptance Criteria:**
- [ ] Receives GitHub webhook events
- [ ] Verifies webhook signatures
- [ ] Events stored and available for analysis
- [ ] Setup guide is clear and complete

---

## Definition of Done

Sprint is complete when:
- [ ] API deployed and accessible
- [ ] GitHub integration working for public repos
- [ ] Webhooks receiving and processing events
- [ ] All tests pass
- [ ] Documentation complete
- [ ] Security review passed (no exposed secrets)

---

## API Design

### Authentication

```
Authorization: Bearer <api_key>
```

API keys stored in environment variables, validated on each request.

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/builds` | Submit batch of build records |
| GET | `/api/v1/analysis` | Get latest analysis results |
| POST | `/api/v1/analyze` | Trigger analysis |
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/webhook/github` | GitHub webhook receiver |

### Example Request

```bash
curl -X POST https://api.devflow-analyzer.app/api/v1/builds \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "builds": [
      {
        "build_id": "12345",
        "project": "myorg/myrepo",
        "status": "passed",
        "duration_seconds": 245,
        "started_at": "2024-01-15T10:30:00Z"
      }
    ]
  }'
```

---

## Security Considerations

| Concern | Mitigation |
|---------|------------|
| API key exposure | Use environment variables, never log keys |
| Webhook spoofing | Verify HMAC signatures |
| Rate limiting | Limit to 100 req/min per API key |
| Data privacy | Don't store sensitive build logs |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| GitHub API rate limits | Cache responses, respect rate limit headers |
| Webhook delivery failures | Implement retry logic, log failures |
| API hosting costs | Start with serverless (Vercel/Railway) |

---

## Sprint Review Checklist

- [ ] API endpoints working and documented
- [ ] GitHub import fetches real data
- [ ] Webhooks receive and process events
- [ ] Security measures in place
- [ ] Performance acceptable
- [ ] Deployed and tested
