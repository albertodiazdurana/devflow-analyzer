# DSM Methodology Feedback

Track methodology effectiveness per section.

| Section | Used? | Score (1-5) | Notes |
|---------|-------|-------------|-------|
| 2.1 Environment Setup | | | |
| 2.2 Exploration | | | |
| 2.3 Feature Engineering | | | |
| 2.4 Analysis | | | |
| 2.5 Communication | | | |
| 3.1 Notebook Structure | | | |
| 3.2 Code Standards | | | |
| DSM_0.2 CLAUDE.md Configuration | Yes | 2 | Critical gap: see entry below |

---

### [2026-02-13] Critical: DSM_0.2 not found by agent due to missing @ reference

**Type:** Methodology Observation
**Priority:** High
**Section:** DSM_0.2 "CLAUDE.md Configuration"
**Score:** 2/5

**Problem:** Agent could not locate DSM_0.2 at session start. The project CLAUDE.md referenced `@..process-mining-llm-reporter_project-knowledge/DSM/` (old DSM path) but DSM_0.2 lives in DSM Central at `/home/berto/dsm-agentic-ai-data-science-methodology/`. Agent searched only the referenced path and reported "No DSM_0.2 file found."

**Root cause:** Two issues compounded:
1. **Missing @ reference:** CLAUDE.md lacked the required `@/path/to/DSM_0.2_Custom_Instructions_v1.1.md` line that DSM_0.2 itself mandates in its "CLAUDE.md Configuration" section.
2. **Stale DSM path:** The `@..process-mining-llm-reporter_project-knowledge/DSM/` path is an older location; DSM Central moved to `~/dsm-agentic-ai-data-science-methodology/`.

**Impact:** Agent operated without DSM_0.2 protocols for the entire session (no session transcript, no pre-generation briefs, no inbox checks per DSM_0.2 spec). Only discovered when user pointed to the correct file path.

**Proposed improvement:** DSM_0.2 "CLAUDE.md Configuration" section should emphasize that the `@` reference is the **discovery mechanism** for DSM_0.2 itself, not just a convention. Without it, the agent cannot find or follow DSM_0.2 protocols. Consider adding a validation step to `/dsm-align` that checks whether the project CLAUDE.md contains a valid `@` reference to DSM_0.2.

**Pushed:** 2026-02-13
