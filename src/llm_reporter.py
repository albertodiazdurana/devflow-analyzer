"""LLM-powered report generator for CI/CD analysis."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .models import BuildAnalysisResult
from .llm_provider import create_llm


@dataclass
class ReportSection:
    """A section of the generated report."""
    title: str
    content: str


@dataclass
class CICDReport:
    """Complete CI/CD analysis report."""
    build_health: ReportSection
    bottleneck_analysis: ReportSection
    failure_patterns: ReportSection
    recommendations: ReportSection
    
    def to_markdown(self) -> str:
        """Format report as markdown."""
        sections = [
            f"# CI/CD Build Analysis Report\n",
            f"## {self.build_health.title}\n{self.build_health.content}\n",
            f"## {self.bottleneck_analysis.title}\n{self.bottleneck_analysis.content}\n",
            f"## {self.failure_patterns.title}\n{self.failure_patterns.content}\n",
            f"## {self.recommendations.title}\n{self.recommendations.content}\n",
        ]
        return "\n".join(sections)


class LLMReporter:
    """Generate natural language reports from CI/CD metrics."""
    
    PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
    
    def __init__(self, model_key: str = "claude-sonnet", temperature: float = 0.7):
        """Initialize reporter with specified model.
        
        Args:
            model_key: Key from AVAILABLE_MODELS
            temperature: Sampling temperature
        """
        self.model_key = model_key
        self.temperature = temperature
        self._llm = None
    
    @property
    def llm(self):
        """Lazy-load LLM instance."""
        if self._llm is None:
            self._llm = create_llm(self.model_key, self.temperature)
        return self._llm
    
    def _load_prompt(self, name: str) -> PromptTemplate:
        """Load a prompt template from file."""
        prompt_path = self.PROMPTS_DIR / f"{name}.txt"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {prompt_path}")
        
        template = prompt_path.read_text()
        
        # Detect variables in template
        variables = []
        if "{metrics}" in template:
            variables.append("metrics")
        if "{analysis}" in template:
            variables.append("analysis")
        
        return PromptTemplate(template=template, input_variables=variables)
    
    def _generate_section(self, prompt_name: str, metrics: str, analysis: str = "") -> str:
        """Generate a single report section."""
        prompt = self._load_prompt(prompt_name)
        chain = prompt | self.llm | StrOutputParser()
        
        inputs = {"metrics": metrics}
        if "analysis" in prompt.input_variables:
            inputs["analysis"] = analysis
        
        return chain.invoke(inputs)
    
    def generate_report(self, analysis_result: BuildAnalysisResult) -> CICDReport:
        """Generate complete report from analysis results.
        
        Args:
            analysis_result: BuildAnalysisResult from ProcessAnalyzer
        
        Returns:
            CICDReport with all sections
        """
        metrics_context = analysis_result.to_llm_context()
        
        # Generate each section
        build_health = self._generate_section("build_health_summary", metrics_context)
        bottleneck = self._generate_section("bottleneck_analysis", metrics_context)
        failures = self._generate_section("failure_patterns", metrics_context)
        
        # Recommendations need prior analysis as context
        prior_analysis = f"""
Build Health Summary:
{build_health}

Bottleneck Analysis:
{bottleneck}

Failure Patterns:
{failures}
"""
        recommendations = self._generate_section("recommendations", metrics_context, prior_analysis)
        
        return CICDReport(
            build_health=ReportSection("Build Health Summary", build_health),
            bottleneck_analysis=ReportSection("Bottleneck Analysis", bottleneck),
            failure_patterns=ReportSection("Failure Patterns", failures),
            recommendations=ReportSection("Recommendations", recommendations),
        )
    
    def generate_section(self, section_name: str, analysis_result: BuildAnalysisResult) -> str:
        """Generate a single section (for testing or partial generation).
        
        Args:
            section_name: One of: build_health_summary, bottleneck_analysis, 
                         failure_patterns, recommendations
            analysis_result: BuildAnalysisResult from ProcessAnalyzer
        
        Returns:
            Generated text for the section
        """
        metrics_context = analysis_result.to_llm_context()
        return self._generate_section(section_name, metrics_context)
