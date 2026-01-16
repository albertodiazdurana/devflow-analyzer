# Sprint 1: Core UX Improvements

**Sprint Goal:** Improve the upload experience and add export capabilities to make the app more user-friendly and practical.

**Duration:** 5 days

**Backlog Items:** B-001, B-002, B-003

---

## Sprint Backlog

### Day 1-3: Column Mapping UI (B-001)

**Objective:** Allow users to upload CSVs with custom column names and map them interactively.

#### Day 1: Backend - Flexible Data Loading

**Tasks:**
- [ ] Modify `ProcessAnalyzer` to accept custom column mappings
- [ ] Create `ColumnMapper` class in `src/column_mapper.py`
- [ ] Add auto-detection of common column name patterns
- [ ] Write unit tests for flexible loading

**Deliverables:**
- `src/column_mapper.py`
- `tests/test_column_mapper.py`
- Updated `src/process_analyzer.py`

**Acceptance Criteria:**
- [ ] Can load CSV with any column names if mapping provided
- [ ] Auto-detects columns matching patterns like `*build_id*`, `*status*`
- [ ] Tests pass

#### Day 2: Frontend - Column Mapping Interface

**Tasks:**
- [ ] Add column preview after file upload (show first 5 rows)
- [ ] Create dropdown selectors for each required column
- [ ] Show auto-detected mappings as defaults
- [ ] Add validation (required columns must be mapped)

**Deliverables:**
- Updated `app.py` Upload tab with mapping UI
- Validation logic

**Acceptance Criteria:**
- [ ] User sees CSV preview after upload
- [ ] Dropdowns populated with CSV column names
- [ ] Auto-detected columns pre-selected
- [ ] Clear error if required columns not mapped

#### Day 3: Polish & Edge Cases

**Tasks:**
- [ ] Handle edge cases (empty files, wrong file types)
- [ ] Add "Reset to defaults" button
- [ ] Add help text explaining each required column
- [ ] Test with various CSV formats
- [ ] Update app documentation

**Deliverables:**
- Robust error handling
- Complete mapping flow

**Acceptance Criteria:**
- [ ] Works with CSVs from different CI/CD systems
- [ ] Clear error messages for invalid files
- [ ] Help text explains what each column should contain

---

### Day 4: Export Reports as PDF/Markdown (B-002)

**Objective:** Add download buttons for Agent analysis as PDF or Markdown.

**Tasks:**
- [ ] Add Markdown export for Agent responses
- [ ] Install `fpdf2` or `weasyprint` for PDF generation
- [ ] Create `src/export.py` with export utilities
- [ ] Add download buttons to Agent tab
- [ ] Include metadata (timestamp, model used, question)

**Deliverables:**
- `src/export.py`
- Download buttons in Agent tab
- Updated `requirements.txt`

**Acceptance Criteria:**
- [ ] "Download as Markdown" button works
- [ ] "Download as PDF" button works
- [ ] Exported files include question, response, metadata
- [ ] PDF is properly formatted

---

### Day 5: LLM Response Caching (B-003)

**Objective:** Cache Agent responses to avoid expensive re-runs for identical questions.

**Tasks:**
- [ ] Create cache key from (question hash + data hash + model + temperature)
- [ ] Implement session-based caching using `st.session_state`
- [ ] Add cache hit/miss indicator in UI
- [ ] Add "Clear Cache" button
- [ ] Consider persistent cache option (SQLite or file-based)

**Deliverables:**
- Caching logic in `app.py`
- Cache status indicator
- Clear cache button

**Acceptance Criteria:**
- [ ] Repeated identical questions return cached response instantly
- [ ] Cache shows "Using cached response" indicator
- [ ] Different questions or settings bypass cache
- [ ] Clear cache button works

---

## Definition of Done

Sprint is complete when:
- [ ] All features deployed to Streamlit Cloud
- [ ] All tests pass (`pytest tests/ -v`)
- [ ] Documentation updated (README, app help text)
- [ ] Demo tested end-to-end
- [ ] Code committed and pushed

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| PDF library complexity | Fall back to Markdown-only if PDF issues |
| Column auto-detection accuracy | Provide manual override for all fields |
| Cache memory usage | Limit cache size, clear old entries |

---

## Sprint Review Checklist

- [ ] Column mapping works for custom CSVs
- [ ] PDF/Markdown export functional
- [ ] Caching reduces API costs
- [ ] User feedback incorporated
- [ ] Deployed and tested on cloud
