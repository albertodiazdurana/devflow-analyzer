### [2026-02-13] Structure misalignments detected

**Type:** Action Item
**Priority:** Medium
**Source:** DSM Central

During DSM Central inbox processing, the following structure misalignments were
identified in devflow-analyzer:

1. **`PROJECT_PLAN.md` in root:** Project plans belong in `docs/plans/`. Move to
   `docs/plans/PROJECT_PLAN.md` (or rename to follow date convention).

2. **`prompts/` in root:** Non-canonical directory. Consider moving to `src/prompts/`
   (if code-adjacent) or `data/prompts/` (if data-adjacent).

3. **Missing canonical docs/ subdirectories:** Run `/dsm-align` to create missing
   folders (decisions/, feedback/, blog/, guides/, plans/, with done/ where applicable).

4. **Stale `@` reference in CLAUDE.md:** Already reported in previous inbox entry.
   Without a valid `@` reference to DSM_0.2, all inherited protocols are disabled.

5. **`mlruns/`:** If MLflow artifacts, ensure this is in `.gitignore` (large binary
   artifacts should not be tracked).

**Reference:** DSM_0.1 Root File Policy (new), DSM_4.0 Section 2.2 project structure.

**Action:** Open a session in devflow-analyzer and run `/dsm-align` after fixing
the CLAUDE.md `@` reference.
