"""Process analyzer for CI/CD build data."""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import BuildAnalysisResult, ProjectMetrics, Bottleneck


class ProcessAnalyzer:
    """Analyze CI/CD build data from TravisTorrent dataset."""

    # Column mappings from TravisTorrent schema
    COLUMN_MAP = {
        "build_id": "tr_build_id",
        "project": "gh_project_name",
        "status": "tr_status",
        "duration": "tr_duration",
        "started_at": "gh_build_started_at",
        "language": "gh_lang",
        "tests_run": "tr_log_num_tests_run",
        "tests_failed": "tr_log_num_tests_failed",
    }

    def __init__(self, data_path: Optional[Path] = None):
        """Initialize analyzer with optional data path."""
        self.data_path = data_path
        self.df: Optional[pd.DataFrame] = None

    def load_data(self, path: Optional[Path] = None) -> pd.DataFrame:
        """Load TravisTorrent CSV data."""
        path = path or self.data_path
        if path is None:
            raise ValueError("No data path provided")

        self.df = pd.read_csv(path)
        self._preprocess()
        return self.df

    def _preprocess(self) -> None:
        """Preprocess loaded data."""
        if self.df is None:
            return

        # Parse timestamp
        ts_col = self.COLUMN_MAP["started_at"]
        if ts_col in self.df.columns:
            self.df[ts_col] = pd.to_datetime(self.df[ts_col], errors="coerce")

        # Ensure numeric columns
        for col in ["duration", "tests_run", "tests_failed"]:
            src_col = self.COLUMN_MAP[col]
            if src_col in self.df.columns:
                self.df[src_col] = pd.to_numeric(self.df[src_col], errors="coerce")

    def analyze(self) -> BuildAnalysisResult:
        """Run full analysis and return structured result."""
        if self.df is None:
            raise ValueError("No data loaded. Call load_data() first.")

        df = self.df
        col = self.COLUMN_MAP

        # Basic counts
        n_builds = len(df)
        n_projects = df[col["project"]].nunique()

        # Date range
        ts_col = col["started_at"]
        date_start = df[ts_col].min() if ts_col in df.columns else None
        date_end = df[ts_col].max() if ts_col in df.columns else None

        # Convert to Python datetime if not NaT
        if pd.notna(date_start):
            date_start = date_start.to_pydatetime()
        else:
            date_start = None
        if pd.notna(date_end):
            date_end = date_end.to_pydatetime()
        else:
            date_end = None

        # Status counts and rates
        status_col = col["status"]
        status_counts = df[status_col].value_counts().to_dict()

        passed = status_counts.get("passed", 0)
        failed = status_counts.get("failed", 0)
        errored = status_counts.get("errored", 0)

        success_rate = passed / n_builds if n_builds > 0 else 0
        failure_rate = failed / n_builds if n_builds > 0 else 0
        error_rate = errored / n_builds if n_builds > 0 else 0

        # Language counts
        lang_col = col["language"]
        language_counts = {}
        if lang_col in df.columns:
            language_counts = df[lang_col].value_counts().to_dict()

        # Duration metrics
        dur_col = col["duration"]
        durations = df[dur_col].dropna()
        median_dur = float(durations.median()) if len(durations) > 0 else 0
        p90_dur = float(durations.quantile(0.9)) if len(durations) > 0 else 0
        max_dur = float(durations.max()) if len(durations) > 0 else 0

        # Project-level metrics
        project_metrics = self._compute_project_metrics()

        # Top failing projects (failure rate > 30% and at least 10 builds)
        top_failing = [
            p for p in project_metrics
            if p.failure_rate > 0.3 and p.n_builds >= 10
        ]
        top_failing = sorted(top_failing, key=lambda x: x.failure_rate, reverse=True)[:5]

        # Projects at risk (high failure rate or high error rate)
        projects_at_risk = [
            p.project for p in project_metrics
            if (p.failure_rate + p.error_rate) > 0.4 and p.n_builds >= 10
        ]

        # Bottlenecks (simplified: identify projects with long build times)
        bottlenecks = self._identify_bottlenecks()

        return BuildAnalysisResult(
            n_builds=n_builds,
            n_projects=n_projects,
            date_range_start=date_start,
            date_range_end=date_end,
            overall_success_rate=success_rate,
            overall_failure_rate=failure_rate,
            overall_error_rate=error_rate,
            median_duration_seconds=median_dur,
            p90_duration_seconds=p90_dur,
            max_duration_seconds=max_dur,
            status_counts=status_counts,
            language_counts=language_counts,
            bottlenecks=bottlenecks,
            projects_at_risk=projects_at_risk,
            top_failing_projects=top_failing,
            project_metrics=project_metrics,
        )

    def _compute_project_metrics(self) -> list[ProjectMetrics]:
        """Compute metrics for each project."""
        if self.df is None:
            return []

        df = self.df
        col = self.COLUMN_MAP
        project_col = col["project"]
        status_col = col["status"]
        dur_col = col["duration"]
        tests_run_col = col["tests_run"]
        tests_failed_col = col["tests_failed"]

        metrics = []
        for project, group in df.groupby(project_col):
            n = len(group)
            status_counts = group[status_col].value_counts()

            passed = status_counts.get("passed", 0)
            failed = status_counts.get("failed", 0)
            errored = status_counts.get("errored", 0)

            durations = group[dur_col].dropna()
            median_dur = float(durations.median()) if len(durations) > 0 else 0
            p90_dur = float(durations.quantile(0.9)) if len(durations) > 0 else 0

            avg_tests_run = None
            avg_tests_failed = None
            if tests_run_col in group.columns:
                tests_run = group[tests_run_col].dropna()
                if len(tests_run) > 0:
                    avg_tests_run = float(tests_run.mean())
            if tests_failed_col in group.columns:
                tests_failed = group[tests_failed_col].dropna()
                if len(tests_failed) > 0:
                    avg_tests_failed = float(tests_failed.mean())

            metrics.append(ProjectMetrics(
                project=project,
                n_builds=n,
                success_rate=passed / n if n > 0 else 0,
                failure_rate=failed / n if n > 0 else 0,
                error_rate=errored / n if n > 0 else 0,
                median_duration_seconds=median_dur,
                p90_duration_seconds=p90_dur,
                avg_tests_run=avg_tests_run,
                avg_tests_failed=avg_tests_failed,
            ))

        return metrics

    def _identify_bottlenecks(self) -> list[Bottleneck]:
        """Identify bottlenecks based on build duration patterns."""
        if self.df is None:
            return []

        df = self.df
        col = self.COLUMN_MAP
        dur_col = col["duration"]
        project_col = col["project"]

        bottlenecks = []

        # Identify projects with significantly longer build times
        project_durations = df.groupby(project_col)[dur_col].median()
        overall_median = df[dur_col].median()

        if pd.isna(overall_median):
            return []

        # Projects with median duration > 2x overall median
        slow_projects = project_durations[project_durations > overall_median * 2]

        for project, duration in slow_projects.items():
            n_builds = len(df[df[project_col] == project])
            bottlenecks.append(Bottleneck(
                transition=f"builds in {project}",
                avg_wait_seconds=float(duration),
                frequency=n_builds,
            ))

        return sorted(bottlenecks, key=lambda x: x.avg_wait_seconds, reverse=True)[:5]

    def generate_dfg(self, output_path: Path) -> Path:
        """Generate Directly-Follows Graph visualization using PM4Py."""
        try:
            import pm4py
            from pm4py.objects.conversion.log import converter as log_converter
            from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
            from pm4py.visualization.dfg import visualizer as dfg_visualization
        except ImportError:
            raise ImportError("PM4Py is required for DFG generation. Install with: pip install pm4py")

        if self.df is None:
            raise ValueError("No data loaded. Call load_data() first.")

        # Prepare data for PM4Py (requires case_id, activity, timestamp)
        col = self.COLUMN_MAP
        pm4py_df = self.df[[col["project"], col["status"], col["started_at"]]].copy()
        pm4py_df.columns = ["case:concept:name", "concept:name", "time:timestamp"]
        pm4py_df = pm4py_df.dropna()

        # Convert to event log
        event_log = log_converter.apply(pm4py_df)

        # Discover DFG
        dfg = dfg_discovery.apply(event_log)

        # Visualize
        gviz = dfg_visualization.apply(dfg, log=event_log, variant=dfg_visualization.Variants.FREQUENCY)

        # Save
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        dfg_visualization.save(gviz, str(output_path))

        return output_path
