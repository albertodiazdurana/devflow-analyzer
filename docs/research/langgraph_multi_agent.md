# Research: LangGraph Multi-Agent Supervisor Patterns

**Purpose/Question:** How to refactor the single ReAct agent into a multi-agent supervisor system using LangGraph?
**Target Outcome:** Architecture and implementation plan for Sprint B (Multi-Agent)
**Status:** Complete
**Date Created:** 2026-02-13

---

## 1. Supervisor Pattern Overview

### Architecture

```
                    [User]
                      |
                 [Supervisor]
                /             \
    [Investigator]    [Root Cause Analyzer]
         |                     |
    [3 tools]             [3-4 tools]
```

The supervisor coordinates routing between specialized agents. Each agent is a `create_react_agent` compiled graph that serves as a node in the supervisor `StateGraph`.

### Why Supervisor (Not Swarm or Hierarchy)

- Clear separation of concerns (routing vs. analysis)
- Extensible (adding a third agent = adding a node)
- Observable (routing decisions visible in message stream for Streamlit UI)
- Portfolio value (most commonly cited multi-agent architecture)

### Package Options

| Package | Version | Recommendation |
|---------|---------|---------------|
| `langgraph` (core) | 1.0.6 (installed) | **Use this.** Has everything needed. |
| `langgraph-supervisor` | 0.0.31 (not installed) | Skip. Pre-1.0, API may change. |
| `langgraph-swarm` | 0.1.0 (not installed) | Skip. Peer-to-peer, wrong pattern. |

**Decision:** Manual `StateGraph` construction. Full control, demonstrates proficiency, no extra dependency.

---

## 2. Core Implementation Pattern

### Shared State

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

class SupervisorState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
```

The `add_messages` reducer is append-only by default. Messages are merged by ID -- new messages get appended, same-ID messages get replaced.

### Supervisor Node with Command Routing

```python
from pydantic import BaseModel
from langgraph.types import Command
from langgraph.graph import END

class RouteDecision(BaseModel):
    next_agent: Literal["investigator", "root_cause_analyzer", "FINISH"]
    reasoning: str

def supervisor_node(state: SupervisorState) -> Command[Literal["investigator", "root_cause_analyzer", "__end__"]]:
    supervisor_llm_structured = llm.with_structured_output(RouteDecision)

    decision = supervisor_llm_structured.invoke([
        {"role": "system", "content": SUPERVISOR_PROMPT},
        *state["messages"],
    ])

    goto = END if decision.next_agent == "FINISH" else decision.next_agent

    return Command(
        update={"messages": [AIMessage(
            content=f"Routing to {decision.next_agent}: {decision.reasoning}",
            name="supervisor"
        )]},
        goto=goto,
    )
```

### Agent Subgraphs as Nodes

`CompiledStateGraph` extends `Pregel` extends `Runnable` -- can be passed directly to `StateGraph.add_node()`.

```python
from langgraph.prebuilt import create_react_agent

investigator = create_react_agent(
    model=llm,
    tools=[get_summary_stats, analyze_bottlenecks, compare_projects],
    prompt=INVESTIGATOR_PROMPT,
    name="investigator",  # Critical: enables subgraph usage
)

root_cause_analyzer = create_react_agent(
    model=llm,
    tools=[get_summary_stats, analyze_failures, temporal_analysis, correlation_detection],
    prompt=ROOT_CAUSE_PROMPT,
    name="root_cause_analyzer",
)
```

### Graph Construction

```python
from langgraph.graph import StateGraph, START, END

builder = StateGraph(SupervisorState)
builder.add_node("supervisor", supervisor_node,
                 destinations=("investigator", "root_cause_analyzer", END))
builder.add_node("investigator", investigator)
builder.add_node("root_cause_analyzer", root_cause_analyzer)

builder.add_edge(START, "supervisor")
builder.add_edge("investigator", "supervisor")
builder.add_edge("root_cause_analyzer", "supervisor")

graph = builder.compile()
```

---

## 3. Routing Strategies

### Hybrid Routing (Recommended)

Rule-based for clear signals, LLM fallback for ambiguous queries:

```python
def hybrid_router(state: SupervisorState) -> Command:
    last_message = state["messages"][-1].content.lower()

    # Clear signals -> rule-based
    if "root cause" in last_message or "why did" in last_message:
        return Command(goto="root_cause_analyzer")
    if "compare" in last_message or "bottleneck" in last_message:
        return Command(goto="investigator")

    # Ambiguous -> LLM decides
    return llm_route(state)
```

### Cost/Latency Consideration

Each LLM-based routing decision adds one API call (~$0.001 with gpt-4o-mini). Rule-based routing is free. Hybrid approach minimizes cost for common cases while handling edge cases.

---

## 4. Agent Specialization Design

### Investigator Agent

**Focus:** WHAT is happening (metrics, bottlenecks, comparisons)

| Tool | Source | Purpose |
|------|--------|---------|
| `get_summary_stats` | Existing | Overview metrics |
| `analyze_bottlenecks` | Existing | Performance bottlenecks |
| `compare_projects` | Existing | Cross-project comparison |

### Root Cause Analyzer Agent

**Focus:** WHY things are happening (failures, patterns, correlations)

| Tool | Source | Purpose |
|------|--------|---------|
| `get_summary_stats` | Existing (shared) | Context for analysis |
| `analyze_failures` | Existing | Failure breakdown |
| `temporal_analysis` | **New** | Time-based pattern detection |
| `correlation_detection` | **New** | Cross-metric correlations |

### Tool Sharing

Both agents can reference the same `@tool`-decorated functions. Tools are stateless -- the global `_current_analysis` context is set once before the supervisor graph runs. No conflicts.

---

## 5. State and Context Management

### Global Analysis Context

The existing `_current_analysis` pattern works for multi-agent because:
1. Agents run sequentially (supervisor routes to one at a time)
2. Both need the same `BuildAnalysisResult`
3. The global is set once before the supervisor graph is invoked

### Cross-Agent Context Passing

Context passes through the shared message list. After the investigator runs, its findings are in the messages. When root_cause_analyzer runs next, it sees those messages.

### Checkpointing

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "session-123"}}
result = graph.invoke({"messages": [("user", "Analyze my CI/CD data")]}, config)
```

---

## 6. Migration Path

### File Structure

```
src/agent.py  →  src/agents/__init__.py
                  src/agents/tools.py           # shared tools + new tools
                  src/agents/investigator.py     # investigator agent
                  src/agents/root_cause.py       # root cause agent
                  src/agents/supervisor.py        # supervisor graph
```

### External API Preserved

```python
# The DevFlowAgent class interface stays the same:
class DevFlowAgent:
    def analyze(self, analysis_result, task=None):
        set_analysis_context(analysis_result)
        result = self.supervisor_graph.invoke({"messages": [("user", task)]})
        return result["messages"][-1].content
```

`app.py` calls `DevFlowAgent.analyze()` and `DevFlowAgent.investigate()` -- no changes needed to the Streamlit app.

---

## 7. API Notes (LangGraph 1.0.6)

- `AgentState` deprecated in langgraph.prebuilt -- use `MessagesState` or custom TypedDict
- `Command` type (from `langgraph.types`) is the modern routing mechanism
- `name=` parameter on `create_react_agent` is the key enabler for multi-agent
- `version="v2"` is the default for `create_react_agent` (uses `Send` for parallel tool execution)
- `config_schema` deprecated in favor of `context_schema`

---

## 8. Testing Strategy

### Unit: Individual Agents

Test that each agent calls expected tools for specific query types.

### Unit: Routing Logic

Test that supervisor routes correctly for clear signals (rule-based) and ambiguous queries (LLM-based with mocked LLM).

### Integration: Full Graph

Test end-to-end supervisor graph execution with mock analysis data. Verify messages from both supervisor and agent nodes appear.

### Mocking

Use `FakeListChatModel` from `langchain_core.language_models.fake_chat_models` for deterministic tests without API calls.

---

## 9. Architecture Decision Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Pattern | Supervisor (not swarm/hierarchy) | Clear control flow, 2-agent system |
| Construction | Manual StateGraph | Full control, no pre-1.0 dependency |
| Routing | Hybrid (rule-based + LLM fallback) | Cost-efficient, handles ambiguity |
| State sharing | Shared messages list | Built-in LangGraph pattern |
| Global context | Preserve `_current_analysis` pattern | Sequential execution, both agents need same data |
| Checkpointing | `InMemorySaver` | Sufficient for Streamlit sessions |
| Migration | `agent.py` → `agents/` package | Clean separation, preserved external API |
