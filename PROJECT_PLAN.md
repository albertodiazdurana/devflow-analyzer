# DevFlow Analyzer - Project Plan v2

## Project Overview

**Repository:** `github.com/albertodiazdurana/devflow-analyzer`

**Tagline:** An agentic ML system that applies process mining to software development workflows, identifies bottlenecks in CI/CD pipelines, and generates actionable insights using LLM-powered natural language generation.

**Problem Statement:** CI/CD pipelines generate valuable data (build logs, durations, failure rates), but translating these into actionable insights requires manual interpretation. This project automates that translation using process mining + LLMs.

**Solution:** An end-to-end agentic pipeline that takes CI/CD event logs, performs process mining analysis, and generates natural language reports with build health assessments, bottleneck explanations, and optimization recommendations.

---

## Strategic Value (JetBrains Application)

| JetBrains Requirement | This Project Demonstrates |
|-----------------------|---------------------------|
| "Design ML systems from scratch" | Full architecture: data pipeline → agent → evaluation |
| "Apply existing models or train custom ones" | LLM integration + optional HuggingFace fine-tuning |
| "AI agents development" | ReAct-style agent with tool-use and iterative refinement |
| "Build training and evaluation pipelines" | MLflow logging, prompt A/B testing, ROUGE metrics |
| "Stay up to date with ML advances" | LangChain, modern agent patterns, multiple providers |
| "Fast iteration and reproducibility" | Modular architecture, configurable prompts, experiment tracking |
| "NLP/code modeling background" | Process mining on software dev workflows (CI/CD, git) |
| "High uncertainty projects" | Agentic approach handles variable data patterns |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              INPUT                                       │
│                    CI/CD Build Logs (TravisTorrent)                     │
│                    Git Event Logs (optional)                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        PROCESS ANALYZER                                  │
│                          (PM4Py)                                        │
├─────────────────────────────────────────────────────────────────────────┤
│  • Import CI/CD event log (CSV → PM4Py format)                         │
│  • Generate Directly-Follows Graph (DFG)                               │
│  • Calculate build statistics (duration, success rate)                 │
│  • Extract workflow variants (build → test → deploy paths)             │
│  • Identify bottlenecks (slow transitions, failure points)             │
│  • Compute KPIs (throughput, cycle time, failure rate)                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     STRUCTURED METRICS                                   │
│                   (BuildAnalysisResult)                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  {                                                                      │
│    "n_builds": 519373,                                                  │
│    "n_projects": 20,                                                    │
│    "success_rate": 0.72,                                                │
│    "median_duration_seconds": 245,                                      │
│    "p90_duration_seconds": 890,                                         │
│    "top_failure_reasons": ["test_failure", "compilation_error"],       │
│    "bottlenecks": [                                                     │
│      {"transition": "build→test", "avg_wait_seconds": 45},             │
│      {"transition": "test→deploy", "avg_wait_seconds": 120}            │
│    ],                                                                   │
│    "projects_at_risk": ["project_a", "project_b"]                      │
│  }                                                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      LLM PROVIDER FACTORY                                │
│                      (Provider-Agnostic)                                │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │  Anthropic  │  │   OpenAI    │  │   Ollama    │  │ HuggingFace │   │
│  │   Claude    │  │   GPT-4     │  │   Local     │  │  (stretch)  │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
│         └────────────────┴────────────────┴────────────────┘          │
│                          Unified Interface                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        DEVFLOW AGENT                                     │
│                    (ReAct Pattern + Tools)                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     AGENT LOOP                                   │   │
│  │  1. Observe: Review metrics                                      │   │
│  │  2. Think: Identify key issues                                   │   │
│  │  3. Act: Call analysis tool                                      │   │
│  │  4. Observe: Review tool output                                  │   │
│  │  5. Repeat until complete                                        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │  Bottleneck │  │   Failure   │  │   Project   │  │   Report    │   │
│  │  Analyzer   │  │   Pattern   │  │   Compare   │  │  Generator  │   │
│  │   Tool      │  │   Tool      │  │   Tool      │  │   Tool      │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      EVALUATION PIPELINE                                 │
│                        (MLflow + Metrics)                               │
├─────────────────────────────────────────────────────────────────────────┤
│  • Log all experiments (prompts, outputs, metrics)                     │
│  • Track prompt versions and A/B tests                                 │
│  • Compute output quality (ROUGE, coherence)                           │
│  • Compare provider performance                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           OUTPUT                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    CI/CD INSIGHTS REPORT                         │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │                                                                  │   │
│  │  BUILD HEALTH SUMMARY                                            │   │
│  │  Analyzed 519,373 builds across 20 Java projects. Overall       │   │
│  │  success rate is 72%, with median build time of 4.1 minutes...  │   │
│  │                                                                  │   │
│  │  BOTTLENECK ANALYSIS                                            │   │
│  │  The primary bottleneck occurs in the test→deploy transition,   │   │
│  │  with average wait time of 2 minutes. This suggests deployment  │   │
│  │  pipeline capacity constraints...                                │   │
│  │                                                                  │   │
│  │  FAILURE PATTERNS                                                │   │
│  │  Test failures account for 45% of broken builds, concentrated   │   │
│  │  in projects X and Y. Compilation errors represent 30%...       │   │
│  │                                                                  │   │
│  │  RECOMMENDATIONS                                                 │   │
│  │  1. Add parallel test execution for projects X, Y               │   │
│  │  2. Implement build caching to reduce compilation time          │   │
│  │  3. Add pre-commit hooks to catch errors earlier                │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  + Process Flow Visualization (DFG PNG)                                │
│  + Raw Metrics (JSON)                                                  │
│  + Experiment Logs (MLflow)                                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
devflow-analyzer/
│
├── README.md                      # Project documentation
├── requirements.txt               # Dependencies
├── .env.example                   # Environment template
├── .gitignore                     # Standard Python gitignore
│
├── app.py                         # Streamlit application
│
├── src/
│   ├── __init__.py
│   ├── models.py                  # Data classes (BuildAnalysisResult, etc.)
│   ├── llm_provider.py            # Provider-agnostic LLM factory
│   ├── process_analyzer.py        # PM4Py wrapper for CI/CD data
│   ├── llm_reporter.py            # LangChain report generation
│   ├── agent.py                   # ReAct agent with tools
│   └── evaluation.py              # MLflow integration, metrics
│
├── prompts/
│   ├── build_health_summary.txt   # Prompt template
│   ├── bottleneck_analysis.txt    # Prompt template
│   ├── failure_patterns.txt       # Prompt template
│   └── recommendations.txt        # Prompt template
│
├── data/
│   ├── sample/                    # Sample CI/CD data (subset)
│   └── README.md                  # Data download instructions
│
├── outputs/
│   ├── figures/                   # DFG visualizations
│   └── reports/                   # Generated reports
│
├── notebooks/
│   └── 01_demo.ipynb              # Demo notebook
│
├── tests/
│   ├── test_models.py
│   ├── test_analyzer.py
│   ├── test_provider.py
│   ├── test_reporter.py
│   ├── test_agent.py
│   └── test_evaluation.py
│
├── docs/
│   ├── architecture.md            # Architecture documentation
│   └── decisions/                 # Decision log
│       └── DEC-001_provider_factory.md
│
└── mlruns/                        # MLflow experiment tracking
```

---

## Implementation Plan

### Day 1: Foundation & Data Pipeline (Phase 0 + Phase 1)

**Objective:** Set up environment and build working CI/CD data analysis pipeline.

#### Part 1: Environment Setup (1 hour)
- Create virtual environment
- Install dependencies (pm4py, langchain, streamlit, mlflow)
- Create directory structure
- Download TravisTorrent sample data

**Deliverables:**
- Working `.venv` with all dependencies
- `requirements.txt`
- `.env.example`
- Sample data in `data/sample/`

#### Part 2: Data Models (1 hour)
- Create `src/models.py` with dataclasses
- `BuildEvent`, `BuildAnalysisResult`, `Bottleneck`
- Serialization methods (to_dict, to_json, to_llm_context)

**Deliverables:**
- `src/models.py`
- `tests/test_models.py`

#### Part 3: Process Analyzer (2-3 hours)
- Create `src/process_analyzer.py`
- Load TravisTorrent CSV data
- Convert to PM4Py event log format
- Calculate build statistics
- Identify bottlenecks and failure patterns
- Generate DFG visualization

**Deliverables:**
- `src/process_analyzer.py`
- `tests/test_analyzer.py`
- Working analysis on sample data

**Day 1 Success Criteria:**
- [x] Environment setup complete
- [x] TravisTorrent data loads successfully
- [x] PM4Py analysis produces valid metrics
- [x] `BuildAnalysisResult` outputs clean JSON
- [x] DFG visualization saves as PNG

---

### Day 2: Core Modules (Phase 2)

**Objective:** Build LLM provider factory and basic report generation.

#### Part 1: LLM Provider Factory (1.5 hours)
- Create `src/llm_provider.py`
- Implement factory pattern with `AVAILABLE_MODELS` registry
- Support Anthropic, OpenAI, Ollama
- Add provider availability checks

**Deliverables:**
- `src/llm_provider.py`
- `tests/test_provider.py`

#### Part 2: Prompt Templates (1 hour)
- Create CI/CD-specific prompts
- `prompts/build_health_summary.txt`
- `prompts/bottleneck_analysis.txt`
- `prompts/failure_patterns.txt`
- `prompts/recommendations.txt`

**Deliverables:**
- 4 prompt template files

#### Part 3: LLM Reporter (2 hours)
- Create `src/llm_reporter.py`
- Implement basic chain-based report generation
- Generate sections from metrics + prompts
- Format full report

**Deliverables:**
- `src/llm_reporter.py`
- Working end-to-end: data → metrics → report

**Day 2 Success Criteria:**
- [x] LLM provider factory working with at least one provider
- [x] All prompt templates created and tested
- [x] LLMReporter generates coherent sections
- [x] Full report generation works end-to-end

---

### Day 3: Agentic System (Phase 3a)

**Objective:** Transform reporter into ReAct-style agent with tools.

#### Part 1: Agent Tools (1.5 hours)
- Define tool interfaces for agent
- `analyze_bottlenecks` tool
- `analyze_failures` tool
- `compare_projects` tool
- `generate_report_section` tool

**Deliverables:**
- Tool definitions in `src/agent.py`

#### Part 2: ReAct Agent (2.5 hours)
- Implement agent loop (Observe → Think → Act)
- Agent decides which analysis to run based on data
- Iterative refinement of recommendations
- Handles edge cases (no bottlenecks, perfect builds)

**Deliverables:**
- `src/agent.py` with working ReAct agent
- `tests/test_agent.py`

#### Part 3: Agent Integration (1 hour)
- Connect agent to process analyzer
- Test full agentic flow
- Compare agent vs. chain outputs

**Deliverables:**
- Working agentic pipeline

**Day 3 Success Criteria:**
- [x] Agent can decide which tools to call
- [x] Agent produces different outputs for different data
- [x] Iterative refinement improves recommendations
- [x] Agent handles edge cases gracefully

---

### Day 4: Evaluation Pipeline (Phase 3b)

**Objective:** Build reproducible experiment tracking and evaluation.

#### Part 1: MLflow Integration (1.5 hours)
- Set up MLflow tracking
- Log experiments (prompts, outputs, metrics)
- Track prompt versions
- Compare runs

**Deliverables:**
- `src/evaluation.py`
- MLflow experiment logging working

#### Part 2: Evaluation Metrics (1.5 hours)
- Implement output quality metrics
- ROUGE scores for report sections
- Coherence/fluency metrics
- Provider comparison framework

**Deliverables:**
- Evaluation metrics in `src/evaluation.py`
- Automated evaluation script

#### Part 3: A/B Testing Framework (1 hour)
- Prompt variant testing
- Statistical comparison of outputs
- Results logging and visualization

**Deliverables:**
- A/B testing capability
- Sample comparison results

**Day 4 Success Criteria:**
- [x] All experiments logged to MLflow
- [x] Evaluation metrics computed automatically
- [x] Can compare prompt variants
- [x] Can compare provider outputs

---

### Day 5: Application & Documentation (Phase 4)

**Objective:** Create interactive demo and complete documentation.

#### Part 1: Streamlit Application (2 hours)
- Build `app.py` with tabs:
  - Upload & Analyze
  - Metrics Dashboard
  - Agent Report
  - Evaluation Results
- Provider selection in sidebar
- Export capabilities

**Deliverables:**
- Working `app.py`

#### Part 2: Documentation (1.5 hours)
- Complete README with:
  - Project overview
  - Architecture diagram
  - Setup instructions
  - Usage examples
  - JetBrains relevance section
- Create `docs/architecture.md`
- Document key decisions

**Deliverables:**
- Complete `README.md`
- `docs/architecture.md`
- Decision log entries

#### Part 3: Demo & Polish (1 hour)
- Create `notebooks/01_demo.ipynb`
- Test full flow end-to-end
- Fix any issues
- Final cleanup

**Deliverables:**
- Demo notebook
- Polished, working repository

**Day 5 Success Criteria:**
- [x] Streamlit app runs without errors
- [x] All features accessible in UI
- [x] README complete and professional
- [x] Demo notebook works end-to-end
- [x] Repository ready for showcase

---

### Stretch: HuggingFace Fine-tuning (Optional)

**Objective:** Add custom model capability to demonstrate training skills.

#### Tasks:
- Fine-tune small model (DistilBERT/CodeT5) on CI/CD terminology
- Add HuggingFace provider to factory
- Compare fine-tuned vs. API outputs
- Document fine-tuning process

**Deliverables:**
- Fine-tuned model
- HuggingFace integration in provider factory
- Comparison results

---

## Success Metrics

### Functional
- [x] End-to-end pipeline works (CI/CD data → analysis → agent → report)
- [x] Agent demonstrates autonomous decision-making
- [x] Multiple LLM providers supported
- [x] Evaluation pipeline produces reproducible results

### Code Quality
- [x] Modular, well-organized codebase
- [x] Type hints on public interfaces
- [x] Unit tests for core modules (86 tests)
- [x] No hardcoded secrets

### Documentation
- [x] README with clear setup instructions
- [x] Architecture diagram
- [x] Decision log for key choices
- [x] Demo notebook

### JetBrains Alignment
- [x] Demonstrates ML system design from scratch
- [x] Shows AI agent development capabilities
- [x] Includes reproducible evaluation pipeline
- [x] Uses modern ML frameworks
- [x] Applies to software development domain (CI/CD)

---

## Data Source

**Primary:** TravisTorrent Java Subset
- 519,373 CI builds from 20 Java projects
- Source: [GitHub](https://github.com/monperrus/travistorrent-java-ci-build-dataset)
- Key fields: build_id, project, status, duration, timestamp, git metadata

**Backup:** Git-logs-for-Process-Mining
- Git commits from 23 projects
- Source: [GitHub](https://github.com/lasaris/Git-logs-for-Process-Mining)

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Process Mining | PM4Py |
| LLM Framework | LangChain |
| LLM Providers | Anthropic, OpenAI, Ollama |
| Agent Pattern | ReAct (LangChain Agents) |
| Experiment Tracking | MLflow |
| UI | Streamlit |
| Testing | pytest |
| Data Processing | pandas, numpy |

---

## Author

**Alberto Diaz Durana**
[GitHub](https://github.com/albertodiazdurana) | [LinkedIn](https://www.linkedin.com/in/albertodiazdurana/)
