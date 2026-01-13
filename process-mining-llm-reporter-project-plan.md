# Process Mining LLM Reporter

## Project Overview

**Repository:** `github.com/albertodiazdurana/process-mining-llm-reporter`

**Tagline:** Transform process mining metrics into executive-ready insights using LLM-powered natural language generation.

**Problem Statement:** Process mining tools like PM4Py generate valuable metrics (bottlenecks, variants, durations), but translating these into actionable business insights requires manual interpretation. This project automates that translation using LLMs.

**Solution:** An end-to-end pipeline that takes event logs, performs process mining analysis, and generates natural language reports with executive summaries, bottleneck explanations, and actionable recommendations.

---

## Strategic Value

### For Your Portfolio
- Demonstrates practical LLM integration (not just tutorials)
- Builds on your existing PM4Py and NLP expertise
- Creates narrative: "Topic Modeling (2021) → LLM Integration (2026)"
- Unique positioning: Process Mining + LLM is uncommon
- **Provider-agnostic architecture** shows software engineering best practices

### For JetBrains Application
| JetBrains Requirement | This Project Demonstrates |
|-----------------------|---------------------------|
| "Apply existing models or train custom ones" | LLM integration with prompt engineering |
| "AI agents development" | Structured LLM workflow for automated reporting |
| "Enhance software development processes" | Applicable to build logs, CI/CD pipelines |
| "Stay up to date with ML advances" | Current LangChain stack, multiple providers |
| "Fast iteration and reproducibility" | Modular architecture, configurable prompts |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              INPUT                                       │
│                         Event Log (CSV/XES)                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        PROCESS ANALYZER                                  │
│                          (PM4Py)                                        │
├─────────────────────────────────────────────────────────────────────────┤
│  • Import event log                                                     │
│  • Generate Directly-Follows Graph (DFG)                               │
│  • Calculate case statistics (duration, frequency)                      │
│  • Extract process variants                                             │
│  • Identify bottlenecks (waiting times between activities)             │
│  • Compute KPIs (throughput, cycle time, rework rate)                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     STRUCTURED METRICS                                   │
│                   (ProcessAnalysisResult)                               │
├─────────────────────────────────────────────────────────────────────────┤
│  {                                                                      │
│    "n_cases": 1250,                                                     │
│    "n_events": 15420,                                                   │
│    "n_activities": 12,                                                  │
│    "n_variants": 45,                                                    │
│    "median_duration_hours": 72.5,                                       │
│    "p90_duration_hours": 168.2,                                         │
│    "top_variant": ["Start", "Review", "Approve", "End"],               │
│    "top_variant_frequency": 0.32,                                       │
│    "bottlenecks": [                                                     │
│      {"from": "Review", "to": "Approve", "avg_wait_hours": 24.5},      │
│      {"from": "Submit", "to": "Review", "avg_wait_hours": 12.3}        │
│    ],                                                                   │
│    "rework_activities": ["Review", "Revision"],                        │
│    "rework_rate": 0.18                                                  │
│  }                                                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      LLM PROVIDER FACTORY                                │
│                      (Provider-Agnostic)                                │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │  Anthropic  │  │   OpenAI    │  │   Ollama    │  │   Future    │   │
│  │   Claude    │  │   GPT-4     │  │   Local     │  │  Providers  │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
│         └────────────────┴────────────────┴────────────────┘          │
│                          Unified Interface                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        LLM REPORTER                                      │
│                    (LangChain Integration)                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│  │   Executive     │  │   Bottleneck    │  │ Recommendations │        │
│  │   Summary       │  │   Analysis      │  │                 │        │
│  │   Prompt        │  │   Prompt        │  │   Prompt        │        │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘        │
│           │                    │                    │                  │
│           ▼                    ▼                    ▼                  │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                      LLM Chain                                   │  │
│  │         metrics + prompt → structured report section            │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           OUTPUT                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    PROCESS INSIGHTS REPORT                       │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │                                                                  │   │
│  │  EXECUTIVE SUMMARY                                               │   │
│  │  The process handled 1,250 cases with a median completion       │   │
│  │  time of 72.5 hours. Overall efficiency is moderate, with       │   │
│  │  18% of cases requiring rework...                               │   │
│  │                                                                  │   │
│  │  BOTTLENECK ANALYSIS                                            │   │
│  │  The primary bottleneck occurs between Review and Approve       │   │
│  │  stages, with an average wait time of 24.5 hours. This         │   │
│  │  suggests resource constraints in the approval function...      │   │
│  │                                                                  │   │
│  │  RECOMMENDATIONS                                                 │   │
│  │  1. Add approval capacity during peak periods                   │   │
│  │  2. Implement parallel review paths for low-risk cases         │   │
│  │  3. Automate initial review for standard requests              │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  + DFG Visualization (PNG)                                             │
│  + Raw Metrics (JSON)                                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Supported LLM Providers

| Provider | Models | Cost (per 1M tokens) | Notes |
|----------|--------|---------------------|-------|
| **Anthropic** | claude-3-haiku, claude-sonnet-4, claude-opus-4 | $0.25-$75 | Default provider |
| **OpenAI** | gpt-4o-mini, gpt-4o | $0.15-$10 | Alternative |
| **Ollama** | llama3, mistral | Free (local) | Offline mode |

---

## Repository Structure

```
process-mining-llm-reporter/
│
├── README.md                      # Project documentation
├── requirements.txt               # Dependencies (multi-provider)
├── .env.example                   # Environment template (multiple API keys)
├── .gitignore                     # Standard Python gitignore
│
├── app.py                         # Streamlit application
│
├── src/
│   ├── __init__.py
│   ├── models.py                  # Data classes for structured output
│   ├── llm_provider.py            # Provider-agnostic LLM factory (NEW)
│   ├── process_analyzer.py        # PM4Py wrapper
│   └── llm_reporter.py            # LangChain integration
│
├── prompts/
│   ├── executive_summary.txt      # Prompt template
│   ├── bottleneck_analysis.txt    # Prompt template
│   └── recommendations.txt        # Prompt template
│
├── data/
│   ├── sample_receipt_log.xes     # PM4Py sample data
│   └── sample_output.json         # Example metrics output
│
├── outputs/
│   └── figures/                   # DFG visualizations
│
├── notebooks/
│   └── 01_exploration.ipynb       # Development notebook
│
└── tests/
    ├── test_process_analyzer.py   # Process analyzer tests
    └── test_llm_provider.py       # Provider factory tests
```

---

## Implementation Plan

### Day 1: Foundation & Data Pipeline

**Objective:** Build working PM4Py analysis pipeline that outputs structured metrics.

#### Morning (3-4 hours)

**Task 1.1: Project Setup**
```bash
# Create repository
mkdir process-mining-llm-reporter
cd process-mining-llm-reporter
git init

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Create directory structure
mkdir -p src prompts data outputs/figures notebooks tests
touch src/__init__.py
```

**Task 1.2: Dependencies**

Create `requirements.txt`:
```
# Core
pm4py>=2.7.0
langchain>=0.1.0
streamlit>=1.30.0
python-dotenv>=1.0.0
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
graphviz>=0.20.0

# LLM Providers (install what you need)
langchain-anthropic>=0.1.0    # Claude (default)
langchain-openai>=0.0.5       # OpenAI (optional)

# Optional: Local models
# langchain-ollama>=0.0.1
```

Install:
```bash
pip install -r requirements.txt
```

**Task 1.3: Environment Configuration**

Create `.env.example`:
```
# LLM Provider Configuration
# Default model key (see src/llm_provider.py for options)
LLM_MODEL=claude-3-haiku

# API Keys (only need the one for your chosen provider)
ANTHROPIC_API_KEY=your-anthropic-key-here
OPENAI_API_KEY=your-openai-key-here
```

Create `.gitignore`:
```
.env
venv/
__pycache__/
*.pyc
.ipynb_checkpoints/
outputs/
*.log
.claude/
```

#### Afternoon (3-4 hours)

**Task 1.4: Data Models**

Create `src/models.py`:
```python
"""
Data models for process mining analysis results.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict
import json


@dataclass
class Bottleneck:
    """Represents a transition bottleneck between two activities."""
    from_activity: str
    to_activity: str
    avg_wait_hours: float
    frequency: int


@dataclass
class ProcessAnalysisResult:
    """Complete process mining analysis results."""
    # Basic counts
    n_cases: int
    n_events: int
    n_activities: int
    n_variants: int

    # Duration metrics
    median_duration_hours: float
    mean_duration_hours: float
    p90_duration_hours: float
    min_duration_hours: float
    max_duration_hours: float

    # Variant analysis
    top_variant: List[str]
    top_variant_frequency: float

    # Bottlenecks
    bottlenecks: List[Bottleneck]

    # Quality metrics
    rework_activities: List[str] = field(default_factory=list)
    rework_rate: float = 0.0

    # Activity statistics
    activity_frequencies: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def to_llm_context(self) -> str:
        """Format metrics for LLM consumption."""
        bottleneck_str = "\n".join([
            f"  - {b.from_activity} -> {b.to_activity}: {b.avg_wait_hours:.1f} hours avg wait ({b.frequency} occurrences)"
            for b in self.bottlenecks[:5]
        ])

        return f"""
PROCESS METRICS:
- Total cases analyzed: {self.n_cases:,}
- Total events: {self.n_events:,}
- Unique activities: {self.n_activities}
- Process variants: {self.n_variants}

DURATION STATISTICS:
- Median case duration: {self.median_duration_hours:.1f} hours
- Mean case duration: {self.mean_duration_hours:.1f} hours
- 90th percentile: {self.p90_duration_hours:.1f} hours
- Range: {self.min_duration_hours:.1f} - {self.max_duration_hours:.1f} hours

MOST COMMON PATH (Happy Path):
- Sequence: {' -> '.join(self.top_variant)}
- Frequency: {self.top_variant_frequency:.1%} of cases

TOP BOTTLENECKS (by wait time):
{bottleneck_str}

QUALITY INDICATORS:
- Rework rate: {self.rework_rate:.1%}
- Activities with rework: {', '.join(self.rework_activities) if self.rework_activities else 'None identified'}
"""
```

**Task 1.5: Process Analyzer**

Create `src/process_analyzer.py`:
```python
"""
PM4Py wrapper for process mining analysis.
"""

import pm4py
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.visualization.dfg import visualizer as dfg_visualizer
from pm4py.statistics.traces.generic.log import case_statistics
from pm4py.algo.filtering.log.variants import variants_filter
import pandas as pd
import numpy as np
from pathlib import Path

from .models import ProcessAnalysisResult, Bottleneck


class ProcessAnalyzer:
    """PM4Py wrapper for process mining analysis."""

    def __init__(self, log_path: str):
        self.log_path = Path(log_path)
        self.log = None
        self.dfg = None
        self.start_activities = None
        self.end_activities = None

    def load_log(self) -> None:
        """Load event log from file."""
        suffix = self.log_path.suffix.lower()

        if suffix == '.xes':
            self.log = xes_importer.apply(str(self.log_path))
        elif suffix == '.csv':
            df = pd.read_csv(self.log_path)
            df = pm4py.format_dataframe(
                df,
                case_id='case_id',
                activity_key='activity',
                timestamp_key='timestamp'
            )
            self.log = pm4py.convert_to_event_log(df)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    def analyze(self) -> ProcessAnalysisResult:
        """Run full process mining analysis."""
        if self.log is None:
            self.load_log()

        # Discover DFG
        self.dfg, self.start_activities, self.end_activities = pm4py.discover_dfg(self.log)

        # Basic statistics
        n_cases = len(self.log)
        n_events = sum(len(trace) for trace in self.log)

        # Activity statistics
        activities = set()
        activity_freq = {}
        for trace in self.log:
            for event in trace:
                act = event['concept:name']
                activities.add(act)
                activity_freq[act] = activity_freq.get(act, 0) + 1

        # Variant analysis
        variants = variants_filter.get_variants(self.log)
        n_variants = len(variants)

        # Top variant
        top_variant_tuple = max(variants.items(), key=lambda x: len(x[1]))
        top_variant = list(top_variant_tuple[0]) if isinstance(top_variant_tuple[0], tuple) else [top_variant_tuple[0]]
        top_variant_freq = len(top_variant_tuple[1]) / n_cases

        # Duration statistics
        case_durations = case_statistics.get_all_case_durations(self.log)
        durations_hours = [d / 3600 for d in case_durations]

        # Bottleneck analysis
        bottlenecks = self._calculate_bottlenecks()

        # Rework detection
        rework_activities, rework_rate = self._detect_rework()

        return ProcessAnalysisResult(
            n_cases=n_cases,
            n_events=n_events,
            n_activities=len(activities),
            n_variants=n_variants,
            median_duration_hours=float(np.median(durations_hours)),
            mean_duration_hours=float(np.mean(durations_hours)),
            p90_duration_hours=float(np.percentile(durations_hours, 90)),
            min_duration_hours=float(np.min(durations_hours)),
            max_duration_hours=float(np.max(durations_hours)),
            top_variant=top_variant,
            top_variant_frequency=top_variant_freq,
            bottlenecks=bottlenecks,
            rework_activities=rework_activities,
            rework_rate=rework_rate,
            activity_frequencies=activity_freq
        )

    def _calculate_bottlenecks(self) -> list[Bottleneck]:
        """Calculate waiting times between activities."""
        transition_times = {}
        transition_counts = {}

        for trace in self.log:
            events = list(trace)
            for i in range(len(events) - 1):
                from_act = events[i]['concept:name']
                to_act = events[i + 1]['concept:name']

                from_time = events[i]['time:timestamp']
                to_time = events[i + 1]['time:timestamp']

                delta_hours = (to_time - from_time).total_seconds() / 3600

                key = (from_act, to_act)
                if key not in transition_times:
                    transition_times[key] = []
                    transition_counts[key] = 0

                transition_times[key].append(delta_hours)
                transition_counts[key] += 1

        bottlenecks = []
        for (from_act, to_act), times in transition_times.items():
            avg_wait = np.mean(times)
            bottlenecks.append(Bottleneck(
                from_activity=from_act,
                to_activity=to_act,
                avg_wait_hours=float(avg_wait),
                frequency=transition_counts[(from_act, to_act)]
            ))

        bottlenecks.sort(key=lambda x: x.avg_wait_hours, reverse=True)
        return bottlenecks[:10]

    def _detect_rework(self) -> tuple[list[str], float]:
        """Detect activities that occur multiple times in cases."""
        rework_activities = set()
        cases_with_rework = 0

        for trace in self.log:
            activity_counts = {}
            for event in trace:
                act = event['concept:name']
                activity_counts[act] = activity_counts.get(act, 0) + 1

            has_rework = False
            for act, count in activity_counts.items():
                if count > 1:
                    rework_activities.add(act)
                    has_rework = True

            if has_rework:
                cases_with_rework += 1

        rework_rate = cases_with_rework / len(self.log) if self.log else 0
        return list(rework_activities), rework_rate

    def save_dfg_visualization(self, output_path: str) -> None:
        """Save DFG as image."""
        if self.dfg is None:
            self.analyze()

        gviz = dfg_visualizer.apply(
            self.dfg,
            activities_count=self.start_activities,
            parameters={dfg_visualizer.Variants.FREQUENCY.value.Parameters.FORMAT: "png"}
        )
        dfg_visualizer.save(gviz, output_path)


if __name__ == "__main__":
    analyzer = ProcessAnalyzer("data/sample_receipt_log.xes")
    result = analyzer.analyze()
    print(result.to_llm_context())
```

**Task 1.6: Test with Sample Data**

```python
# In notebook or script
import pm4py
from pm4py.objects.log.exporter.xes import exporter as xes_exporter

# Get sample log
log = pm4py.read_xes(pm4py.get_event_log_path())
xes_exporter.apply(log, "data/sample_receipt_log.xes")
```

**Day 1 Success Criteria:**
- [ ] Repository initialized with proper structure
- [ ] PM4Py successfully analyzes sample event log
- [ ] ProcessAnalysisResult dataclass outputs clean JSON
- [ ] `to_llm_context()` produces readable metrics string
- [ ] DFG visualization saves as PNG

---

### Day 2: LLM Integration (Provider-Agnostic)

**Objective:** Build provider-agnostic LangChain pipeline that transforms metrics into natural language reports.

#### Morning (3-4 hours)

**Task 2.1: LLM Provider Factory (NEW)**

Create `src/llm_provider.py`:
```python
"""
Provider-agnostic LLM factory.

Supports multiple backends with a unified interface.
"""

from dataclasses import dataclass
from typing import Optional
import os
from dotenv import load_dotenv

from langchain_core.language_models.chat_models import BaseChatModel

load_dotenv()


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    provider: str
    model_id: str
    display_name: str
    cost_per_1k_input: float
    cost_per_1k_output: float


# Available models registry
AVAILABLE_MODELS: dict[str, ModelConfig] = {
    # Anthropic
    "claude-3-haiku": ModelConfig(
        provider="anthropic",
        model_id="claude-3-haiku-20240307",
        display_name="Claude 3 Haiku (Fast)",
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.00125,
    ),
    "claude-sonnet": ModelConfig(
        provider="anthropic",
        model_id="claude-sonnet-4-20250514",
        display_name="Claude Sonnet 4 (Balanced)",
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
    ),
    "claude-opus": ModelConfig(
        provider="anthropic",
        model_id="claude-opus-4-20250514",
        display_name="Claude Opus 4 (Best)",
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
    ),
    # OpenAI
    "gpt-4o-mini": ModelConfig(
        provider="openai",
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini (Fast)",
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
    ),
    "gpt-4o": ModelConfig(
        provider="openai",
        model_id="gpt-4o",
        display_name="GPT-4o (Best)",
        cost_per_1k_input=0.0025,
        cost_per_1k_output=0.01,
    ),
    # Ollama (local)
    "ollama-llama3": ModelConfig(
        provider="ollama",
        model_id="llama3",
        display_name="Llama 3 (Local)",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
    ),
}


class LLMProviderError(Exception):
    """Raised when LLM provider configuration fails."""
    pass


def get_available_models(provider: Optional[str] = None) -> list[str]:
    """Get list of available model keys, optionally filtered by provider."""
    if provider:
        return [k for k, v in AVAILABLE_MODELS.items() if v.provider == provider]
    return list(AVAILABLE_MODELS.keys())


def get_model_config(model_key: str) -> ModelConfig:
    """Get configuration for a specific model."""
    if model_key not in AVAILABLE_MODELS:
        raise LLMProviderError(f"Unknown model: {model_key}")
    return AVAILABLE_MODELS[model_key]


def create_llm(
    model_key: Optional[str] = None,
    temperature: float = 0.3,
) -> BaseChatModel:
    """
    Factory function to create an LLM instance.

    Args:
        model_key: Key from AVAILABLE_MODELS (e.g., "claude-3-haiku")
        temperature: Sampling temperature (0.0 - 1.0)

    Returns:
        Configured LangChain chat model
    """
    if model_key is None:
        model_key = os.getenv("LLM_MODEL", "claude-3-haiku")

    config = get_model_config(model_key)

    if config.provider == "anthropic":
        return _create_anthropic(config, temperature)
    elif config.provider == "openai":
        return _create_openai(config, temperature)
    elif config.provider == "ollama":
        return _create_ollama(config, temperature)
    else:
        raise LLMProviderError(f"Unsupported provider: {config.provider}")


def _create_anthropic(config: ModelConfig, temperature: float) -> BaseChatModel:
    """Create Anthropic Claude instance."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise LLMProviderError("ANTHROPIC_API_KEY not set")

    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        raise LLMProviderError("langchain-anthropic not installed")

    return ChatAnthropic(
        model=config.model_id,
        temperature=temperature,
        api_key=api_key,
    )


def _create_openai(config: ModelConfig, temperature: float) -> BaseChatModel:
    """Create OpenAI instance."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMProviderError("OPENAI_API_KEY not set")

    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise LLMProviderError("langchain-openai not installed")

    return ChatOpenAI(
        model=config.model_id,
        temperature=temperature,
        api_key=api_key,
    )


def _create_ollama(config: ModelConfig, temperature: float) -> BaseChatModel:
    """Create Ollama (local) instance."""
    try:
        from langchain_ollama import ChatOllama
    except ImportError:
        raise LLMProviderError("langchain-ollama not installed")

    return ChatOllama(
        model=config.model_id,
        temperature=temperature,
    )


def check_provider_available(provider: str) -> tuple[bool, str]:
    """Check if a provider is properly configured."""
    if provider == "anthropic":
        if os.getenv("ANTHROPIC_API_KEY"):
            return True, "Anthropic API configured"
        return False, "ANTHROPIC_API_KEY not set"

    elif provider == "openai":
        if os.getenv("OPENAI_API_KEY"):
            return True, "OpenAI API configured"
        return False, "OPENAI_API_KEY not set"

    elif provider == "ollama":
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.ok:
                return True, "Ollama running locally"
        except Exception:
            pass
        return False, "Ollama not running"

    return False, f"Unknown provider: {provider}"
```

**Task 2.2: Prompt Templates**

Create `prompts/executive_summary.txt`:
```
You are a senior process analyst preparing an executive summary for business stakeholders.

Given the following process mining metrics:
{metrics}

Write a 3-paragraph executive summary that includes:

1. OVERVIEW: State the scale of analysis (cases, events) and overall process health assessment. Compare median vs mean duration to identify if outliers are skewing performance.

2. EFFICIENCY ASSESSMENT: Evaluate the process efficiency. Consider:
   - Is the happy path dominant (>50%) or is there high variation?
   - How does the 90th percentile compare to median? (Large gap = inconsistent performance)
   - What does the rework rate indicate about quality?

3. KEY CONCERN: Identify the single most important issue leadership should focus on, based on the bottleneck data and rework indicators.

Write in a professional, concise tone. Use specific numbers from the metrics. Avoid jargon.
```

Create `prompts/bottleneck_analysis.txt`:
```
You are a process improvement consultant analyzing workflow bottlenecks.

Given the following process metrics:
{metrics}

Provide a detailed bottleneck analysis with:

1. PRIMARY BOTTLENECK: Identify the transition with the longest average wait time. Explain:
   - Which activities are involved
   - The magnitude of the delay (hours/days)
   - Potential root causes (resource constraints, dependencies, approvals)

2. SECONDARY BOTTLENECKS: List 2-3 other significant delays and their likely causes.

3. PATTERN ANALYSIS: Look at the bottleneck sequence. Are delays concentrated:
   - At the beginning (intake problems)?
   - In the middle (processing capacity)?
   - At the end (approval/closure issues)?

4. IMPACT QUANTIFICATION: Estimate how much the primary bottleneck contributes to total cycle time.

Be specific with numbers. Suggest hypotheses for root causes that could be validated with stakeholders.
```

Create `prompts/recommendations.txt`:
```
You are a process optimization expert providing actionable recommendations.

Given the following process analysis:
{metrics}

Provide exactly 5 prioritized recommendations:

For each recommendation:
- NUMBER and TITLE (e.g., "1. Implement Parallel Review Paths")
- PROBLEM: What specific issue from the metrics does this address?
- ACTION: Concrete steps to implement
- EXPECTED IMPACT: Quantified improvement estimate (e.g., "Reduce cycle time by 15-20%")
- EFFORT: Low / Medium / High implementation effort

Prioritize recommendations by impact-to-effort ratio (quick wins first).

Focus on:
- Bottleneck reduction
- Rework elimination
- Variant consolidation (if too many paths exist)
- Resource optimization

Be practical and specific. Avoid generic advice.
```

**Task 2.3: LLM Reporter Module (Updated)**

Create `src/llm_reporter.py`:
```python
"""
LLM-powered report generation from process mining metrics.
"""

from pathlib import Path
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from .models import ProcessAnalysisResult
from .llm_provider import create_llm, get_model_config, AVAILABLE_MODELS


class LLMReporter:
    """Generate natural language reports from process metrics using LLM."""

    def __init__(self, model_key: str = "claude-3-haiku", temperature: float = 0.3):
        """
        Initialize the reporter with specified model.

        Args:
            model_key: Key from AVAILABLE_MODELS
            temperature: Sampling temperature (0.0 - 1.0)
        """
        self.model_key = model_key
        self.model_config = get_model_config(model_key)
        self.llm = create_llm(model_key, temperature)
        self.prompts_dir = Path(__file__).parent.parent / "prompts"

    @property
    def provider_name(self) -> str:
        """Get the current provider name."""
        return self.model_config.provider

    @property
    def model_display_name(self) -> str:
        """Get human-readable model name."""
        return self.model_config.display_name

    def _load_prompt(self, name: str) -> str:
        """Load prompt template from file."""
        prompt_path = self.prompts_dir / f"{name}.txt"
        return prompt_path.read_text()

    def _generate_section(self, prompt_name: str, metrics: ProcessAnalysisResult) -> str:
        """Generate a single report section."""
        prompt_template = self._load_prompt(prompt_name)
        prompt = PromptTemplate(
            input_variables=["metrics"],
            template=prompt_template
        )

        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = chain.run(metrics=metrics.to_llm_context())
        return result.strip()

    def generate_executive_summary(self, metrics: ProcessAnalysisResult) -> str:
        """Generate executive summary section."""
        return self._generate_section("executive_summary", metrics)

    def generate_bottleneck_analysis(self, metrics: ProcessAnalysisResult) -> str:
        """Generate bottleneck analysis section."""
        return self._generate_section("bottleneck_analysis", metrics)

    def generate_recommendations(self, metrics: ProcessAnalysisResult) -> str:
        """Generate recommendations section."""
        return self._generate_section("recommendations", metrics)

    def generate_full_report(self, metrics: ProcessAnalysisResult) -> dict:
        """Generate complete report with all sections."""
        return {
            "executive_summary": self.generate_executive_summary(metrics),
            "bottleneck_analysis": self.generate_bottleneck_analysis(metrics),
            "recommendations": self.generate_recommendations(metrics),
            "model_used": self.model_display_name,
        }

    def format_report(self, report: dict) -> str:
        """Format report sections into single document."""
        return f"""
================================================================================
                        PROCESS INSIGHTS REPORT
================================================================================
Generated by: {report.get('model_used', 'Unknown')}

EXECUTIVE SUMMARY
-----------------
{report['executive_summary']}

BOTTLENECK ANALYSIS
-------------------
{report['bottleneck_analysis']}

RECOMMENDATIONS
---------------
{report['recommendations']}

================================================================================
"""
```

#### Afternoon (3-4 hours)

**Task 2.4: Test and Refine**

Create `notebooks/01_exploration.ipynb` and test with different providers.

**Day 2 Success Criteria:**
- [ ] LLM provider factory working with Anthropic
- [ ] Provider switching via environment variable
- [ ] All three prompt templates created and tested
- [ ] LLMReporter generates coherent sections
- [ ] Full report flows logically

---

### Day 3: Demo & Documentation

**Objective:** Create Streamlit app with provider selection and complete documentation.

#### Morning (3-4 hours)

**Task 3.1: Streamlit Application (Updated)**

Create `app.py`:
```python
import streamlit as st
import tempfile
from pathlib import Path

from src.process_analyzer import ProcessAnalyzer
from src.llm_reporter import LLMReporter
from src.llm_provider import (
    AVAILABLE_MODELS,
    check_provider_available,
    get_model_config,
)

st.set_page_config(
    page_title="Process Mining LLM Reporter",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Process Mining LLM Reporter")
st.markdown("Transform event logs into executive-ready insights using AI")

# Sidebar - Provider Configuration
with st.sidebar:
    st.header("LLM Configuration")

    # Check which providers are available
    providers = {}
    for key, config in AVAILABLE_MODELS.items():
        if config.provider not in providers:
            providers[config.provider] = []
        providers[config.provider].append((key, config))

    st.subheader("Provider Status")
    available_models = []
    for provider in providers:
        is_available, message = check_provider_available(provider)
        status = "✅" if is_available else "❌"
        st.caption(f"{status} {provider.title()}: {message}")
        if is_available:
            available_models.extend([k for k, _ in providers[provider]])

    if not available_models:
        st.error("No LLM providers configured. Set API keys in .env file.")
        st.stop()

    # Model selector
    st.subheader("Select Model")
    model_key = st.selectbox(
        "Model",
        options=available_models,
        format_func=lambda x: f"{AVAILABLE_MODELS[x].display_name}",
        index=0
    )

    config = get_model_config(model_key)
    st.caption(f"Provider: {config.provider.title()}")
    st.caption(f"Cost: ${config.cost_per_1k_input:.4f}/1K in, ${config.cost_per_1k_output:.4f}/1K out")

    temperature = st.slider("Temperature", 0.0, 1.0, 0.3)

    st.divider()
    st.header("About")
    st.markdown("""
    This tool:
    1. Analyzes event logs with PM4Py
    2. Extracts process metrics
    3. Generates insights using LLM

    [GitHub](https://github.com/albertodiazdurana/process-mining-llm-reporter)
    """)

# Main content tabs
tab1, tab2, tab3 = st.tabs(["📁 Upload & Analyze", "📈 Metrics", "📝 Report"])

with tab1:
    st.header("Upload Event Log")

    uploaded_file = st.file_uploader(
        "Choose a file (CSV or XES)",
        type=["csv", "xes"]
    )

    with st.expander("CSV Format Requirements"):
        st.markdown("""
        Your CSV should have these columns:
        - `case_id`: Unique identifier for each process instance
        - `activity`: Name of the activity/step
        - `timestamp`: When the activity occurred (ISO format)
        """)

    if uploaded_file:
        suffix = Path(uploaded_file.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        with st.spinner("Analyzing process..."):
            try:
                analyzer = ProcessAnalyzer(tmp_path)
                metrics = analyzer.analyze()
                st.session_state['metrics'] = metrics
                st.session_state['analyzer'] = analyzer
                st.success(f"Analysis complete: {metrics.n_cases:,} cases, {metrics.n_events:,} events")
            except Exception as e:
                st.error(f"Error analyzing file: {e}")

with tab2:
    st.header("Process Metrics")

    if 'metrics' in st.session_state:
        metrics = st.session_state['metrics']

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Cases", f"{metrics.n_cases:,}")
        col2.metric("Total Events", f"{metrics.n_events:,}")
        col3.metric("Activities", metrics.n_activities)
        col4.metric("Variants", metrics.n_variants)

        col1, col2, col3 = st.columns(3)
        col1.metric("Median Duration", f"{metrics.median_duration_hours:.1f}h")
        col2.metric("90th Percentile", f"{metrics.p90_duration_hours:.1f}h")
        col3.metric("Rework Rate", f"{metrics.rework_rate:.1%}")

        st.subheader("Happy Path (Most Common)")
        st.write(" -> ".join(metrics.top_variant))
        st.caption(f"Frequency: {metrics.top_variant_frequency:.1%} of cases")

        st.subheader("Top Bottlenecks")
        for b in metrics.bottlenecks[:5]:
            st.write(f"**{b.from_activity} -> {b.to_activity}**: {b.avg_wait_hours:.1f}h avg wait")

        st.subheader("Process Flow (DFG)")
        if 'analyzer' in st.session_state:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                st.session_state['analyzer'].save_dfg_visualization(tmp.name)
                st.image(tmp.name)

        with st.expander("Raw Metrics (JSON)"):
            st.json(metrics.to_dict())
    else:
        st.info("Upload an event log to see metrics")

with tab3:
    st.header("AI-Generated Report")

    if 'metrics' in st.session_state:
        metrics = st.session_state['metrics']

        if st.button("Generate Report", type="primary"):
            try:
                reporter = LLMReporter(model_key=model_key, temperature=temperature)

                with st.spinner(f"Generating report using {reporter.model_display_name}..."):
                    report = reporter.generate_full_report(metrics)

                st.session_state['report'] = report
            except Exception as e:
                st.error(f"Error generating report: {e}")

        if 'report' in st.session_state:
            report = st.session_state['report']

            st.caption(f"Generated by: {report.get('model_used', 'Unknown')}")

            st.subheader("Executive Summary")
            st.write(report['executive_summary'])

            st.subheader("Bottleneck Analysis")
            st.write(report['bottleneck_analysis'])

            st.subheader("Recommendations")
            st.write(report['recommendations'])

            full_report = f"""PROCESS INSIGHTS REPORT
Generated by: {report.get('model_used', 'Unknown')}

EXECUTIVE SUMMARY
{report['executive_summary']}

BOTTLENECK ANALYSIS
{report['bottleneck_analysis']}

RECOMMENDATIONS
{report['recommendations']}
"""
            st.download_button(
                "Download Report",
                full_report,
                file_name="process_report.txt",
                mime="text/plain"
            )
    else:
        st.info("Upload and analyze an event log first")
```

**Task 3.2: Test Application**
```bash
streamlit run app.py
```

#### Afternoon (3-4 hours)

**Task 3.3: README Documentation** - Include provider-agnostic features

**Day 3 Success Criteria:**
- [ ] Streamlit app runs without errors
- [ ] Provider selection works in UI
- [ ] All three tabs functional
- [ ] README complete with architecture diagram
- [ ] Repository public and polished

---

## Stretch Goals

| Feature | Description | Effort |
|---------|-------------|--------|
| RAG Context | Add document retrieval for "why does this bottleneck occur?" questions | Medium |
| PDF Export | Generate formatted PDF report | Low |
| Compare Logs | Upload two logs, LLM explains differences | Medium |
| Local LLM | Ollama integration for offline use | Low (included in provider factory) |
| Caching | Cache LLM responses to reduce API costs | Low |

---

## Success Metrics

After completing this project, you can claim:

- [x] Built LLM-powered reporting system
- [x] **Provider-agnostic architecture** supporting multiple LLM backends
- [x] Integrated LangChain with domain-specific prompts
- [x] Created end-to-end ML application (data → analysis → NLG)
- [x] Deployed interactive Streamlit demo
- [x] Extended existing process mining expertise with LLM capabilities

This directly addresses JetBrains' requirement for "applying existing models" and "AI agents development."

---

Good luck! This project will significantly strengthen your application.
