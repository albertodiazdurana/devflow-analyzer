"""ReAct-style agent for CI/CD analysis."""

from typing import Optional
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from .models import BuildAnalysisResult
from .llm_provider import create_llm


# Global state to hold analysis result for tools
_current_analysis: Optional[BuildAnalysisResult] = None


def set_analysis_context(analysis: BuildAnalysisResult) -> None:
    """Set the analysis result for tools to access."""
    global _current_analysis
    _current_analysis = analysis


@tool
def analyze_bottlenecks() -> str:
    """Analyze build bottlenecks and slow projects in detail.
    
    Returns detailed information about projects with slow builds,
    including duration statistics and comparisons to baseline.
    """
    if _current_analysis is None:
        return "Error: No analysis data available."
    
    result = _current_analysis
    lines = ["## Bottleneck Analysis\n"]
    
    if not result.bottlenecks:
        lines.append("No significant bottlenecks detected.")
        lines.append(f"Median build duration: {result.median_duration_seconds:.0f}s")
        lines.append(f"P90 build duration: {result.p90_duration_seconds:.0f}s")
        return "\n".join(lines)
    
    lines.append(f"Overall median duration: {result.median_duration_seconds:.0f}s ({result.median_duration_seconds/60:.1f} min)")
    lines.append(f"Overall P90 duration: {result.p90_duration_seconds:.0f}s ({result.p90_duration_seconds/60:.1f} min)")
    lines.append(f"\n### Slow Projects (>{result.median_duration_seconds*2:.0f}s median):\n")
    
    for b in result.bottlenecks:
        ratio = b.avg_wait_seconds / result.median_duration_seconds if result.median_duration_seconds > 0 else 0
        lines.append(f"- **{b.transition}**: {b.avg_wait_seconds:.0f}s avg ({ratio:.1f}x baseline), {b.frequency} builds")
    
    return "\n".join(lines)


@tool
def analyze_failures() -> str:
    """Analyze failure patterns across projects.
    
    Returns information about projects with high failure rates,
    failure vs error distribution, and projects at risk.
    """
    if _current_analysis is None:
        return "Error: No analysis data available."
    
    result = _current_analysis
    lines = ["## Failure Pattern Analysis\n"]
    
    lines.append(f"Overall success rate: {result.overall_success_rate:.1%}")
    lines.append(f"Overall failure rate: {result.overall_failure_rate:.1%}")
    lines.append(f"Overall error rate: {result.overall_error_rate:.1%}")
    
    if result.status_counts:
        lines.append(f"\n### Status Distribution:")
        for status, count in sorted(result.status_counts.items(), key=lambda x: -x[1]):
            pct = count / result.n_builds * 100
            lines.append(f"- {status}: {count} ({pct:.1f}%)")
    
    if result.top_failing_projects:
        lines.append(f"\n### Top Failing Projects:")
        for p in result.top_failing_projects:
            lines.append(f"- **{p.project}**: {p.failure_rate:.1%} failure rate, {p.error_rate:.1%} error rate ({p.n_builds} builds)")
    
    if result.projects_at_risk:
        lines.append(f"\n### Projects at Risk (>40% failure+error):")
        for p in result.projects_at_risk:
            lines.append(f"- {p}")
    
    return "\n".join(lines)


@tool
def compare_projects() -> str:
    """Compare metrics across all projects.
    
    Returns a comparison table of all projects with their
    success rates, durations, and test statistics.
    """
    if _current_analysis is None:
        return "Error: No analysis data available."
    
    result = _current_analysis
    lines = ["## Project Comparison\n"]
    
    if not result.project_metrics:
        lines.append("No project-level metrics available.")
        return "\n".join(lines)
    
    lines.append(f"Total projects: {result.n_projects}")
    lines.append(f"Total builds: {result.n_builds}")
    lines.append("")
    
    # Sort by failure rate descending
    sorted_projects = sorted(result.project_metrics, key=lambda x: x.failure_rate, reverse=True)
    
    lines.append("| Project | Builds | Success | Failure | Median Duration |")
    lines.append("|---------|--------|---------|---------|-----------------|")
    
    for p in sorted_projects[:15]:  # Top 15
        lines.append(f"| {p.project[:30]} | {p.n_builds} | {p.success_rate:.0%} | {p.failure_rate:.0%} | {p.median_duration_seconds:.0f}s |")
    
    if len(sorted_projects) > 15:
        lines.append(f"| ... and {len(sorted_projects) - 15} more projects | | | | |")
    
    return "\n".join(lines)


@tool
def get_summary_stats() -> str:
    """Get high-level summary statistics of the CI/CD data.
    
    Returns key metrics like total builds, date range,
    overall success rate, and duration statistics.
    """
    if _current_analysis is None:
        return "Error: No analysis data available."
    
    result = _current_analysis
    return result.to_llm_context()


# System prompt for the agent
SYSTEM_PROMPT = """You are a CI/CD analytics expert. Your task is to analyze build data and provide actionable insights.

When analyzing CI/CD data:
1. First get summary statistics to understand the overall picture
2. Investigate bottlenecks and slow builds
3. Analyze failure patterns and identify problematic projects
4. Compare projects to find outliers
5. Provide specific, actionable recommendations

Focus on the most impactful findings and prioritize your recommendations."""


class DevFlowAgent:
    """ReAct agent for CI/CD analysis."""

    def __init__(self, model_key: str = "gpt-4o-mini", temperature: float = 0.3):
        """Initialize agent with specified model.

        Args:
            model_key: Key from AVAILABLE_MODELS
            temperature: Sampling temperature (lower = more focused)
        """
        self.model_key = model_key
        self.temperature = temperature
        self._agent = None

    def _create_agent(self):
        """Create the ReAct agent using langgraph."""
        llm = create_llm(self.model_key, self.temperature)

        tools = [
            get_summary_stats,
            analyze_bottlenecks,
            analyze_failures,
            compare_projects,
        ]

        # langgraph's create_react_agent returns a compiled graph
        return create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)

    @property
    def agent(self):
        """Lazy-load agent."""
        if self._agent is None:
            self._agent = self._create_agent()
        return self._agent
    
    def analyze(self, analysis_result: BuildAnalysisResult, task: str = None) -> str:
        """Run agent analysis on the build data.

        Args:
            analysis_result: BuildAnalysisResult from ProcessAnalyzer
            task: Optional specific task. Defaults to full analysis.

        Returns:
            Agent's analysis and recommendations
        """
        # Set global context for tools
        set_analysis_context(analysis_result)

        if task is None:
            task = """Analyze this CI/CD build data comprehensively:
1. First get the summary statistics to understand the overall picture
2. Investigate any bottlenecks or slow builds
3. Analyze failure patterns and identify problematic projects
4. Compare projects to find outliers
5. Provide specific, actionable recommendations to improve CI/CD performance

Focus on the most impactful findings and prioritize your recommendations."""

        # langgraph uses messages format
        result = self.agent.invoke({"messages": [("user", task)]})

        # Extract final message content
        if result.get("messages"):
            return result["messages"][-1].content
        return "No output generated"

    def investigate(self, analysis_result: BuildAnalysisResult, question: str) -> str:
        """Ask a specific question about the build data.

        Args:
            analysis_result: BuildAnalysisResult from ProcessAnalyzer
            question: Specific question to investigate

        Returns:
            Agent's response to the question
        """
        set_analysis_context(analysis_result)
        result = self.agent.invoke({"messages": [("user", question)]})

        # Extract final message content
        if result.get("messages"):
            return result["messages"][-1].content
        return "No output generated"
