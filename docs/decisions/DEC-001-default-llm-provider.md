# DEC-001: Default LLM Provider for Agent

**Category:** Library Choice

**Date:** 2026-01-14

**Status:** Accepted

---

## Context

The DevFlow agent uses LangGraph's `create_react_agent` which requires LLMs with **native tool calling** support. Tool calling allows the model to invoke functions directly via structured JSON rather than parsing text output.

Our initial default was `ollama-llama3` (Llama 3 running locally via Ollama) for cost-free development. However, when testing the agent end-to-end, we encountered:

```
ollama._types.ResponseError: registry.ollama.ai/library/llama3:latest does not support tools
```

Llama 3 (base) does not support native tool calling, which langgraph requires.

---

## Decision

Use **GPT-4o-mini** as the default LLM for the agent.

**Changes made:**
- `src/agent.py`: Changed default `model_key` from `"ollama-llama3"` to `"gpt-4o-mini"`

---

## Alternatives Considered

### 1. GPT-4o-mini (Selected)
- **Cost:** $0.15 input / $0.60 output per 1M tokens (cheapest cloud option)
- **Tool support:** Full native tool calling
- **Quality:** Comparable to GPT-4 for simple tasks
- **Latency:** Fast (~1-2s for typical agent queries)

### 2. Claude Haiku
- **Cost:** $1.00 input / $5.00 output per 1M tokens
- **Tool support:** Full native tool calling
- **Quality:** Excellent reasoning
- **Rejected because:** ~6-10x more expensive than GPT-4o-mini for similar capability

### 3. Ollama with tool-capable model (llama3.1, mistral)
- **Cost:** Free (local)
- **Tool support:** Varies by model version
- **Rejected because:** Requires user to pull specific models; inconsistent tool support across versions; adds setup complexity

### 4. Text-based ReAct fallback
- **Cost:** Free with any model
- **Tool support:** Not required (parses "Action:"/"Observation:" from text)
- **Rejected because:** Less reliable; requires prompt engineering; doesn't follow modern LLM patterns

---

## Consequences

### Positive
- Agent works out-of-the-box with OpenAI API key
- Reliable tool calling with structured responses
- Very low cost (~$0.001 per agent analysis)
- Fast response times

### Negative
- Requires OpenAI API key and prepaid credits
- Not free like local Ollama
- Adds external dependency

### Mitigations
- Provider factory (`llm_provider.py`) still supports Ollama for users who prefer local inference
- Users can override default: `DevFlowAgent(model_key="ollama-mistral")`
- Cost is minimal (~$5 covers hundreds of analyses)

---

## References

- [OpenAI Pricing](https://openai.com/api/pricing/)
- [Anthropic Pricing](https://docs.anthropic.com/en/docs/about-claude/models)
- [LangGraph Tool Calling](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/#tool-calling-agent)
