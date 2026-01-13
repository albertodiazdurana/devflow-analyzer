"""Data models for DevFlow Analyzer."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
import json


@dataclass
class BuildEvent:
    """Single CI/CD build event."""
    
    build_id: str
    project: str
    status: str  # passed, failed, errored, canceled
    duration_seconds: Optional[float]
    started_at: Optional[datetime]
    language: Optional[str] = None
    tests_run: Optional[int] = None
    tests_failed: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary with serializable datetime."""
        d = asdict(self)
        if d["started_at"]:
            d["started_at"] = d["started_at"].isoformat()
        return d


@dataclass
class Bottleneck:
    """Identified bottleneck in the build process."""
    
    transition: str  # e.g., "build → test"
    avg_wait_seconds: float
    frequency: int  # number of occurrences
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProjectMetrics:
    """Metrics for a single project."""
    
    project: str
    n_builds: int
    success_rate: float
    failure_rate: float
    error_rate: float
    median_duration_seconds: float
    p90_duration_seconds: float
    avg_tests_run: Optional[float] = None
    avg_tests_failed: Optional[float] = None
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class BuildAnalysisResult:
    """Complete analysis result for CI/CD builds."""
    
    # Summary statistics
    n_builds: int
    n_projects: int
    date_range_start: Optional[datetime]
    date_range_end: Optional[datetime]
    
    # Overall metrics
    overall_success_rate: float
    overall_failure_rate: float
    overall_error_rate: float
    
    # Duration metrics
    median_duration_seconds: float
    p90_duration_seconds: float
    max_duration_seconds: float
    
    # Breakdowns
    status_counts: dict = field(default_factory=dict)
    language_counts: dict = field(default_factory=dict)
    
    # Bottlenecks and issues
    bottlenecks: list[Bottleneck] = field(default_factory=list)
    projects_at_risk: list[str] = field(default_factory=list)
    top_failing_projects: list[ProjectMetrics] = field(default_factory=list)
    
    # Project-level metrics
    project_metrics: list[ProjectMetrics] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        d = {
            "n_builds": self.n_builds,
            "n_projects": self.n_projects,
            "date_range_start": self.date_range_start.isoformat() if self.date_range_start else None,
            "date_range_end": self.date_range_end.isoformat() if self.date_range_end else None,
            "overall_success_rate": self.overall_success_rate,
            "overall_failure_rate": self.overall_failure_rate,
            "overall_error_rate": self.overall_error_rate,
            "median_duration_seconds": self.median_duration_seconds,
            "p90_duration_seconds": self.p90_duration_seconds,
            "max_duration_seconds": self.max_duration_seconds,
            "status_counts": self.status_counts,
            "language_counts": self.language_counts,
            "bottlenecks": [b.to_dict() for b in self.bottlenecks],
            "projects_at_risk": self.projects_at_risk,
            "top_failing_projects": [p.to_dict() for p in self.top_failing_projects],
            "project_metrics": [p.to_dict() for p in self.project_metrics],
        }
        return d
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def to_llm_context(self) -> str:
        """Format as context string for LLM prompts."""
        lines = [
            "# CI/CD Build Analysis Results",
            "",
            "## Summary",
            f"- Total builds analyzed: {self.n_builds:,}",
            f"- Projects: {self.n_projects}",
            f"- Date range: {self.date_range_start} to {self.date_range_end}",
            "",
            "## Build Status",
            f"- Success rate: {self.overall_success_rate:.1%}",
            f"- Failure rate: {self.overall_failure_rate:.1%}",
            f"- Error rate: {self.overall_error_rate:.1%}",
            "",
            "## Duration",
            f"- Median: {self.median_duration_seconds:.0f}s ({self.median_duration_seconds/60:.1f} min)",
            f"- P90: {self.p90_duration_seconds:.0f}s ({self.p90_duration_seconds/60:.1f} min)",
            f"- Max: {self.max_duration_seconds:.0f}s ({self.max_duration_seconds/60:.1f} min)",
            "",
        ]
        
        if self.bottlenecks:
            lines.append("## Bottlenecks")
            for b in self.bottlenecks:
                lines.append(f"- {b.transition}: avg wait {b.avg_wait_seconds:.0f}s ({b.frequency} occurrences)")
            lines.append("")
        
        if self.projects_at_risk:
            lines.append("## Projects at Risk")
            for p in self.projects_at_risk:
                lines.append(f"- {p}")
            lines.append("")
        
        if self.top_failing_projects:
            lines.append("## Top Failing Projects")
            for p in self.top_failing_projects:
                lines.append(f"- {p.project}: {p.failure_rate:.1%} failure rate ({p.n_builds} builds)")
            lines.append("")
        
        return "\n".join(lines)
