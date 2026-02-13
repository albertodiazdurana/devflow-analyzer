# Sprint B: Multi-Agent Orchestration

**Sprint Goal:** Refactor the single ReAct agent into a two-agent supervisor system with an Investigator and Root Cause Analyzer.

**Duration:** 4 days

**Prerequisites:** Sprint A complete (vector store tool available for both agents)

**Research:** [docs/research/langgraph_multi_agent.md](../research/langgraph_multi_agent.md)

---

## Sprint Backlog

### Day 1: Agent Package Refactor + Root Cause Tools

**Objective:** Restructure agent.py into an agents/ package and create new tools for root cause analysis.

**Tasks:**
- [ ] Create `src/agents/` package:
  - `src/agents/__init__.py` — exports `DevFlowAgent`, `set_analysis_context`
  - `src/agents/tools.py` — move all existing tools from `agent.py`:
    - `get_summary_stats`, `analyze_bottlenecks`, `analyze_failures`, `compare_projects`
    - Keep `_current_analysis` global and `set_analysis_context()` here
    - Add `search_historical_analyses` (from Sprint A)
- [ ] Create new root cause tools in `src/agents/tools.py`:
  - `temporal_analysis` — detect time-based patterns (failure spikes, seasonal trends, duration regressions)
  - `correlation_detection` — find correlations between metrics (test count vs duration, language vs failure rate)
- [ ] Update `src/agents/__init__.py` to re-export tools
- [ ] Deprecate/redirect `src/agent.py` → `src/agents/` (keep import compatibility for `app.py`)
- [ ] Write tests for new tools: `tests/test_agent_tools.py`

**Deliverables:**
- `src/agents/__init__.py`
- `src/agents/tools.py` (existing + 2 new tools)
- `tests/test_agent_tools.py`
- `src/agent.py` updated as compatibility shim

**Acceptance Criteria:**
- [ ] Existing `from src.agent import DevFlowAgent` still works
- [ ] New tools return meaningful analysis from BuildAnalysisResult
- [ ] All existing tests pass
- [ ] New tool tests pass

---

### Day 2: Investigator + Root Cause Agents

**Objective:** Create the two specialized agents with distinct tool sets and system prompts.

**Tasks:**
- [ ] Create `src/agents/investigator.py`:
  - `INVESTIGATOR_PROMPT` — focused on "WHAT is happening" (metrics, bottlenecks, comparisons)
  - `create_investigator(llm)` — returns `create_react_agent(model, tools, prompt, name="investigator")`
  - Tools: `get_summary_stats`, `analyze_bottlenecks`, `compare_projects`, `search_historical_analyses`
- [ ] Create `src/agents/root_cause.py`:
  - `ROOT_CAUSE_PROMPT` — focused on "WHY things are happening" (failures, patterns, correlations)
  - `create_root_cause_analyzer(llm)` — returns `create_react_agent(model, tools, prompt, name="root_cause_analyzer")`
  - Tools: `get_summary_stats`, `analyze_failures`, `temporal_analysis`, `correlation_detection`
- [ ] Write tests for each agent:
  - Investigator calls expected tools for metrics questions
  - Root Cause Analyzer calls expected tools for "why" questions
  - Both handle empty/missing analysis gracefully

**Deliverables:**
- `src/agents/investigator.py`
- `src/agents/root_cause.py`
- `tests/test_investigator.py`
- `tests/test_root_cause.py`

**Acceptance Criteria:**
- [ ] Each agent runs independently with correct tools
- [ ] System prompts guide tool selection appropriately
- [ ] Tests pass (with mocked LLM for deterministic tests)

---

### Day 3: Supervisor Graph

**Objective:** Build the LangGraph supervisor that routes between the two agents.

**Tasks:**
- [ ] Create `src/agents/supervisor.py`:
  - `SupervisorState(TypedDict)` — `messages: Annotated[list[AnyMessage], add_messages]`
  - `RouteDecision(BaseModel)` — structured output for routing: `next_agent`, `reasoning`
  - `supervisor_node(state)` — hybrid routing:
    1. Rule-based for clear signals ("root cause", "why", "compare", "bottleneck")
    2. LLM fallback with `with_structured_output(RouteDecision)` for ambiguous queries
  - `build_supervisor_graph(llm)` — constructs and compiles the StateGraph:
    - Nodes: supervisor, investigator, root_cause_analyzer
    - Edges: START→supervisor, investigator→supervisor, root_cause_analyzer→supervisor
    - Supervisor uses `Command` routing to agents or END
  - `InMemorySaver` checkpointing
- [ ] Update `DevFlowAgent` class in `src/agents/__init__.py`:
  - Constructor: `__init__(self, model_key, vector_store=None, mode="supervisor")`
  - `mode="supervisor"`: uses supervisor graph (default)
  - `mode="single"`: uses single ReAct agent (backward compatibility)
  - `analyze()` and `investigate()` methods dispatch to correct graph
- [ ] Write tests: `tests/test_supervisor.py`:
  - Rule-based routing correctness
  - LLM routing with mocked structured output
  - Full graph execution with mock analysis
  - Supervisor terminates (reaches END) after analysis

**Deliverables:**
- `src/agents/supervisor.py`
- Updated `src/agents/__init__.py` (DevFlowAgent with supervisor)
- `tests/test_supervisor.py`

**Acceptance Criteria:**
- [ ] Supervisor routes metrics questions to investigator
- [ ] Supervisor routes "why" questions to root cause analyzer
- [ ] Full graph executes and produces coherent output
- [ ] Supervisor terminates (does not loop infinitely)
- [ ] Tests pass

---

### Day 4: UI Integration + End-to-End Testing

**Objective:** Integrate multi-agent system into Streamlit UI and complete testing.

**Tasks:**
- [ ] Update `app.py` Agent tab:
  - Show active agent indicator ("Routing to: Investigator" / "Root Cause Analyzer")
  - Display routing decision and reasoning
  - Show which agent(s) contributed to the response
  - Optional: collapsible sections for each agent's response
- [ ] Integration testing:
  - End-to-end: upload → analyze → agent query → multi-agent response
  - Test both supervisor and single-agent modes
  - Test agent handoff (investigator finds issue, root cause analyzes it)
  - Test with real OpenAI API calls (gpt-4o-mini)
- [ ] Update README with Sprint B features
- [ ] Move `docs/plans/SPRINT_B.md` to `docs/plans/done/`

**Deliverables:**
- Updated `app.py` (multi-agent UI)
- Integration tests
- Updated README

**Acceptance Criteria:**
- [ ] UI shows routing decisions and agent attributions
- [ ] Multi-agent produces more detailed analysis than single agent
- [ ] Backward compatibility: single-agent mode still works
- [ ] Streamlit Cloud deployment works
- [ ] All tests pass

---

## File Structure After Sprint B

```
src/agents/
    __init__.py          # DevFlowAgent class, exports
    tools.py             # All tools (existing + new)
    investigator.py      # Investigator agent
    root_cause.py        # Root Cause Analyzer agent
    supervisor.py        # Supervisor graph
src/agent.py             # Compatibility shim → imports from agents/
```

---

## Key Architecture Decisions

| Decision | Choice | Reference |
|----------|--------|-----------|
| Pattern | Supervisor (not swarm/hierarchy) | Research doc §1 |
| Construction | Manual StateGraph (not langgraph-supervisor) | Research doc §1 |
| Routing | Hybrid: rule-based + LLM fallback | Research doc §3 |
| State | Shared messages, global _current_analysis | Research doc §5 |
| Checkpointing | InMemorySaver | Research doc §5 |

---

## Risks

| Risk | Mitigation |
|------|------------|
| Supervisor loops infinitely | Max iterations limit, terminate after 2 agent rounds |
| Routing accuracy | Hybrid routing covers common cases; LLM handles edge cases |
| Cost increase (extra LLM calls) | Rule-based routing minimizes LLM routing calls |
| Agent.py backward compatibility | Shim module re-exports from agents/ |
