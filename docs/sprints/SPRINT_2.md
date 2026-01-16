# Sprint 2: Analytics & Visualization

**Sprint Goal:** Add advanced analytics capabilities with time-series analysis, project drill-down, and automatic anomaly detection.

**Duration:** 5 days

**Backlog Items:** B-004, B-005, B-006

**Prerequisites:** Sprint 1 completed

---

## Sprint Backlog

### Day 1-2: Time-Series Analysis (B-004)

**Objective:** Add trend charts showing how success rates, build durations, and failure rates change over time.

#### Day 1: Data Aggregation & Backend

**Tasks:**
- [ ] Add time-series aggregation to `ProcessAnalyzer`
  - Daily/weekly/monthly rollups
  - Success rate over time
  - Average duration over time
  - Failure count over time
- [ ] Create `TimeSeriesMetrics` dataclass in `models.py`
- [ ] Write unit tests for aggregation logic

**Deliverables:**
- `TimeSeriesMetrics` dataclass
- `ProcessAnalyzer.get_time_series()` method
- `tests/test_analyzer.py` updates

**Acceptance Criteria:**
- [ ] Can aggregate metrics by day/week/month
- [ ] Handles sparse data (days with no builds)
- [ ] Tests pass

#### Day 2: Frontend - Time-Series Charts

**Tasks:**
- [ ] Add new "Trends" section to Metrics tab
- [ ] Create line charts using Streamlit's native charts or Plotly
  - Success rate trend
  - Build duration trend (median + P90)
  - Failure/error count trend
- [ ] Add date range selector
- [ ] Add granularity selector (daily/weekly/monthly)

**Deliverables:**
- Trends section in Metrics tab
- Interactive charts with selectors

**Acceptance Criteria:**
- [ ] Charts render correctly
- [ ] Date range filter works
- [ ] Granularity switch updates charts
- [ ] Works on Streamlit Cloud

---

### Day 3-4: Project Drill-Down (B-005)

**Objective:** Click on a project to see detailed build history and project-specific analysis.

#### Day 3: Backend - Project Detail Data

**Tasks:**
- [ ] Add `ProcessAnalyzer.get_project_detail(project_name)` method
  - Recent builds list (last 50)
  - Build history timeline
  - Project-specific success/failure trends
  - Common failure reasons for this project
- [ ] Create `ProjectDetail` dataclass
- [ ] Write unit tests

**Deliverables:**
- `ProjectDetail` dataclass
- `get_project_detail()` method
- Tests

**Acceptance Criteria:**
- [ ] Returns detailed data for specific project
- [ ] Handles projects with few builds gracefully
- [ ] Tests pass

#### Day 4: Frontend - Project Detail Modal/Page

**Tasks:**
- [ ] Make project names clickable in Metrics tab
- [ ] Create project detail view (expandable section or modal)
  - Build history table (status, duration, timestamp)
  - Mini trend chart for this project
  - "Ask Agent about this project" button
- [ ] Add "Back to overview" navigation

**Deliverables:**
- Clickable project names
- Project detail view
- Navigation

**Acceptance Criteria:**
- [ ] Clicking project shows detailed view
- [ ] Build history table is sortable
- [ ] "Ask Agent" pre-fills question about project
- [ ] Can navigate back to overview

---

### Day 5: Anomaly Detection (B-006)

**Objective:** Automatically flag unusual patterns (failure spikes, unusually slow builds) using statistical methods.

**Tasks:**
- [ ] Create `src/anomaly_detector.py`
- [ ] Implement detection algorithms:
  - Z-score for build duration outliers
  - Percentage change detection for success rate drops
  - Streak detection (consecutive failures)
- [ ] Create `Anomaly` dataclass with severity levels
- [ ] Add anomaly badges to Metrics dashboard
- [ ] Add "Anomalies" section highlighting issues
- [ ] Write tests for detection logic

**Deliverables:**
- `src/anomaly_detector.py`
- `Anomaly` dataclass
- `tests/test_anomaly_detector.py`
- Anomaly badges in UI

**Acceptance Criteria:**
- [ ] Detects unusually slow builds (>2 std dev)
- [ ] Detects sudden failure rate increases (>20% change)
- [ ] Detects failure streaks (3+ consecutive)
- [ ] Anomalies displayed with severity (warning/critical)
- [ ] No false positives on normal data

---

## Definition of Done

Sprint is complete when:
- [ ] All features deployed to Streamlit Cloud
- [ ] All tests pass (`pytest tests/ -v`)
- [ ] Documentation updated
- [ ] Charts render correctly on all screen sizes
- [ ] Code committed and pushed

---

## Technical Notes

### Charting Library Options

| Library | Pros | Cons |
|---------|------|------|
| `st.line_chart` | Built-in, simple | Limited customization |
| Plotly | Interactive, professional | Larger bundle |
| Altair | Declarative, Streamlit native | Learning curve |

**Recommendation:** Start with Plotly for interactivity.

### Anomaly Detection Thresholds

| Anomaly Type | Warning | Critical |
|--------------|---------|----------|
| Duration outlier | >2 std dev | >3 std dev |
| Success rate drop | >15% decrease | >30% decrease |
| Failure streak | 3 consecutive | 5 consecutive |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Large datasets slow chart rendering | Downsample data for charts, show max 1000 points |
| Anomaly false positives | Make thresholds configurable |
| Project detail overload | Paginate build history, limit to 50 recent |

---

## Sprint Review Checklist

- [ ] Time-series trends visible and interactive
- [ ] Project drill-down provides useful detail
- [ ] Anomalies auto-detected and highlighted
- [ ] Performance acceptable with 10k+ builds
- [ ] Deployed and tested on cloud
