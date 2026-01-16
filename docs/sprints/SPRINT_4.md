# Sprint 4: Advanced Features

**Sprint Goal:** Add power-user features including multi-dataset comparison, custom prompts, and user authentication for team use.

**Duration:** 5 days

**Backlog Items:** B-010, B-011, B-012

**Prerequisites:** Sprint 1, 2 & 3 completed

---

## Sprint Backlog

### Day 1-2: Multi-Dataset Comparison (B-010)

**Objective:** Compare metrics across different time periods or different datasets (e.g., "this month vs last month").

#### Day 1: Backend - Comparison Logic

**Tasks:**
- [ ] Create `src/comparison.py` with comparison utilities
- [ ] Implement `DatasetComparison` dataclass:
  - Holds two `BuildAnalysisResult` objects
  - Computes deltas for all metrics
  - Identifies significant changes
- [ ] Add comparison methods:
  - `compare_time_periods(df, period1, period2)`
  - `compare_datasets(result1, result2)`
- [ ] Calculate percentage changes and trends
- [ ] Write unit tests

**Deliverables:**
- `src/comparison.py`
- `DatasetComparison` dataclass
- `tests/test_comparison.py`

**Acceptance Criteria:**
- [ ] Can compare two analysis results
- [ ] Calculates meaningful deltas
- [ ] Identifies improvements vs regressions
- [ ] Tests pass

#### Day 2: Frontend - Comparison UI

**Tasks:**
- [ ] Add "Compare" tab or section to app
- [ ] Allow selection of comparison type:
  - Time period comparison (date ranges)
  - Upload second dataset
- [ ] Create comparison visualization:
  - Side-by-side metrics
  - Delta indicators (↑↓)
  - Highlight significant changes
- [ ] Add "Ask Agent to explain changes" button

**Deliverables:**
- Comparison UI in app
- Side-by-side visualization
- Agent integration

**Acceptance Criteria:**
- [ ] Can compare two time periods
- [ ] Can compare two uploaded datasets
- [ ] Deltas clearly displayed
- [ ] Agent can explain changes

---

### Day 3: Custom Prompts (B-011)

**Objective:** Allow users to edit or provide custom prompts for the Agent to tailor analysis to their specific needs.

**Tasks:**
- [ ] Add "Advanced Settings" expander in Agent tab
- [ ] Create prompt template editor:
  - Show current system prompt
  - Allow user modifications
  - Provide template variables reference
- [ ] Add preset prompts for common use cases:
  - "Focus on test failures"
  - "Emphasize performance issues"
  - "Executive summary style"
- [ ] Save custom prompts to session state
- [ ] Add "Reset to default" option
- [ ] Warn about prompt injection risks

**Deliverables:**
- Prompt editor UI
- Preset prompts
- Session persistence

**Acceptance Criteria:**
- [ ] Can edit system prompt
- [ ] Preset prompts available
- [ ] Changes reflected in Agent responses
- [ ] Reset works correctly
- [ ] No security vulnerabilities

---

### Day 4-5: Authentication & Multi-User (B-012)

**Objective:** Add user accounts so teams can have private datasets and shared experiment history.

#### Day 4: Authentication Setup

**Tasks:**
- [ ] Choose auth provider (Streamlit native, Auth0, or custom)
- [ ] Implement login/logout flow
- [ ] Create user session management
- [ ] Add protected routes (require login for certain features)
- [ ] Store user preferences

**Deliverables:**
- Authentication flow
- User session handling
- Protected routes

**Acceptance Criteria:**
- [ ] Users can sign up and log in
- [ ] Session persists across page refreshes
- [ ] Logout works correctly

#### Day 5: User Data & Teams

**Tasks:**
- [ ] Create user data storage (SQLite or cloud database)
- [ ] Implement per-user data:
  - Saved datasets
  - Analysis history
  - Custom prompts
- [ ] Add data export for users
- [ ] Implement basic team features (optional):
  - Invite team members
  - Share datasets within team
- [ ] Add privacy controls

**Deliverables:**
- User data storage
- Personal dashboard
- Data export

**Acceptance Criteria:**
- [ ] Each user has private data
- [ ] Analysis history persisted
- [ ] Can export personal data
- [ ] Privacy controls work

---

## Definition of Done

Sprint is complete when:
- [ ] All features deployed
- [ ] All tests pass
- [ ] Security audit passed (auth, data isolation)
- [ ] Documentation updated
- [ ] User data properly isolated
- [ ] GDPR considerations addressed (data export, deletion)

---

## Authentication Options

| Option | Pros | Cons |
|--------|------|------|
| Streamlit Auth | Simple, built-in | Limited features |
| Auth0 | Full-featured, secure | External dependency |
| Custom (JWT) | Full control | More work |

**Recommendation:** Start with Streamlit's native auth or Auth0 free tier.

---

## Data Storage Options

| Option | Pros | Cons |
|--------|------|------|
| SQLite | Simple, no server | Not scalable |
| Supabase | PostgreSQL, free tier | External service |
| Firebase | Real-time, auth included | Google lock-in |

**Recommendation:** Supabase for persistence with good free tier.

---

## Security Considerations

| Concern | Mitigation |
|---------|------------|
| Prompt injection | Sanitize user prompts, limit length |
| Data isolation | Strict user ID checks on all queries |
| Session hijacking | Secure cookies, HTTPS only |
| Data export | Include only user's own data |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Auth complexity | Start with simple email/password |
| Database costs | Use free tiers, monitor usage |
| Scope creep | Limit team features to MVP |

---

## Sprint Review Checklist

- [ ] Multi-dataset comparison working
- [ ] Custom prompts functional and safe
- [ ] Users can create accounts
- [ ] User data properly isolated
- [ ] Export/delete user data works
- [ ] Security review passed
- [ ] Deployed and tested

---

## Post-Sprint: Stretch Goals

After Sprint 4, consider these for future work:

| Feature | Description | Effort |
|---------|-------------|--------|
| GitLab Integration | Similar to GitHub integration | 2 days |
| Slack Notifications | Send summaries to team channels | 1 day |
| Scheduled Reports | Auto-generate weekly reports | 2 days |
| Fine-tuned Model | Custom model for CI/CD | 5 days |
