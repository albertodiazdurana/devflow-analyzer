# Project Memory

# add this \\wsl.localhost\Ubuntu\home\berto\process-mining-llm-reporter_project-knowledge

[@..](\\wsl.localhost\Ubuntu\home\berto\process-mining-llm-reporter_project-knowledge/DSM)/process-mining-llm-reporter-project-plan-v2.md

# Quick Reference Data Science Methodology (DSM)
@..process-mining-llm-reporter_project-knowledge/DSM/
This document serves as a quick reference guide for the Data Science Methodology (DSM) used in this project. It outlines key paths, document references, author information, working style, code output standards, notebook development protocol, app development protocol, command execution guidelines, and plan mode protocol.

## Key Paths
- Methodology: DSM_1.0_Data_Science_Collaboration_Methodology_v1.1.md
- Appendices: DSM_1.0_Methodology_Appendices.md
- PM Guidelines: DSM_2.0_ProjectManagement_Guidelines_v2_v1.1.md

## Document References
- Environment Setup: Section 2.1
- Exploration: Section 2.2
- Feature Engineering: Section 2.3
- Analysis: Section 2.4
- Communication: Section 2.5
- Session Management: Section 6.1

## Author
**Alberto Diaz Durana**
[GitHub](https://github.com/albertodiazdurana) | [LinkedIn](https://www.linkedin.com/in/albertodiazdurana/)


## Working Style
- Confirm understanding before proceeding
- Be concise in answers
- Do not generate files before providing description and receiving approval

## Code Output Standards
- Print statements show actual values (shapes, metrics, counts)
- Avoid generic confirmations: "Complete!", "Done!", "Success!"
- Let results speak: Show df.shape, not "Data loaded successfully!"

## Notebook Development Protocol
When generating notebook cells:
1. Generate ONE cell at a time; unless the first cell contains markdown only, then generate up to TWO cells
2. Wait for user approval OR execution output before generating next cell
3. Never generate multiple cells without explicit request
4. Adapt each cell based on actual output from previous cells
5. Number each cell with a comment (e.g., `# Cell 1`, `# Cell 2`) for easy reference in discussions

Interaction pattern:
- User describes goal -> Agent proposes cell -> User approves/runs -> Agent sees output -> Agent generates next cell
- "Continue" or "yes" = generate next cell
- "Generate all cells" = explicit batch override

## App Development Protocol

When building application code (packages, modules, scripts):
1. Guide step by step through the development process
2. Explain **why** before each action
3. Provide code segments for user to copy/paste
4. Wait for user confirmation before proceeding to next step
5. Generate no files directly - user creates all artifacts
6. Build modules incrementally: imports → constants → one function → test → next function
7. Use Test-Driven Development (TDD): write tests in `tests/` alongside code

**Interaction pattern:**
- Claude explains purpose → provides code → user creates file → user confirms → next step
- "Done" or "next" = proceed to next step
- "Explain more" = deeper explanation before proceeding

Why: This establishes a learning-focused protocol where you remain in control of file creation, ensuring you understand each piece as it's built. Different from the notebook protocol which is about incremental cell generation.

## Command Execution
- Execute read-only commands (git status, ls, cat, grep, find, python -c for reading) without asking
- Show write commands (git commit, git push, rm, mv, pip install, file edits) for my approval first

## Plan Mode Protocol
Before implementing any significant feature or change:
1. Thoroughly explore the codebase to understand existing patterns
2. Identify similar features and architectural approaches
3. Consider multiple approaches and their trade-offs
4. Ask clarifying questions if approach is unclear
5. Design a concrete implementation strategy
6. Present plan for user approval before writing/editing any files

This is a read-only exploration and planning phase - DO NOT write or edit files until plan is approved.