"""DevFlow Analyzer - Streamlit Application."""

import os
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

# Load secrets from Streamlit Cloud into environment variables
# This must happen BEFORE importing modules that use dotenv
try:
    # Only works on Streamlit Cloud or with local secrets.toml
    for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
        if key in st.secrets:
            os.environ[key] = st.secrets[key]
except FileNotFoundError:
    # No secrets file found - will use .env file via dotenv
    pass

from src.process_analyzer import ProcessAnalyzer
from src.agent import DevFlowAgent
from src.llm_provider import get_available_models, check_provider_available, Provider
from src.evaluation import ExperimentTracker, Timer, compute_cost


# Page configuration
st.set_page_config(
    page_title="DevFlow Analyzer",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "analyzer" not in st.session_state:
    st.session_state.analyzer = None
if "dfg_path" not in st.session_state:
    st.session_state.dfg_path = None
if "run_history" not in st.session_state:
    st.session_state.run_history = []  # Track agent runs for Evaluation tab


def render_sidebar():
    """Render sidebar with configuration options."""
    st.sidebar.title("⚙️ Configuration")

    # Help expander
    with st.sidebar.expander("ℹ️ What is this?", expanded=False):
        st.markdown("""
        **DevFlow Analyzer** helps you understand your CI/CD pipeline health by:

        1. **Analyzing build data** - Upload CSV files with build history
        2. **Visualizing patterns** - See how builds flow between states
        3. **AI-powered insights** - Ask questions and get recommendations

        Start by uploading data in the first tab!
        """)

    st.sidebar.markdown("---")

    # Model selection - OpenAI models only
    st.sidebar.markdown("### 🤖 AI Model Settings")

    openai_models = ["gpt-4o-mini", "gpt-4o"]

    selected_model = st.sidebar.selectbox(
        "LLM Model",
        openai_models,
        index=0,  # gpt-4o-mini is default
        help="Choose which AI model to use. GPT-4o-mini is recommended (fast and cheap).",
    )

    # Model explanation
    with st.sidebar.expander("Which model should I use?"):
        st.markdown("""
        **Recommended:** `gpt-4o-mini`
        - Fast and affordable ($0.15 per 1M input tokens)
        - Good for most analyses

        **Premium:** `gpt-4o`
        - Higher quality responses
        - Better for complex questions
        - More expensive ($5 per 1M input tokens)
        """)

    # Temperature
    temperature = st.sidebar.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.1,
        help="Controls AI creativity. Lower = more consistent, Higher = more varied responses.",
    )

    # Temperature explanation
    with st.sidebar.expander("What is Temperature?"):
        st.markdown("""
        **Temperature** controls how "creative" the AI is:

        - **0.0 - 0.3**: Focused & consistent (best for analysis)
        - **0.4 - 0.7**: Balanced
        - **0.8 - 1.0**: Creative & varied (may be less accurate)

        **Tip:** Keep it at 0.3 for reliable CI/CD analysis.
        """)

    # Provider status - OpenAI only
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔌 Provider Status")

    available, msg = check_provider_available(Provider.OPENAI)
    status = "🟢 Connected" if available else "🔴 Not available"
    st.sidebar.markdown(f"**OpenAI:** {status}")

    if not available:
        st.sidebar.warning("OpenAI API key required. Add it in Settings → Secrets.")

    return selected_model, temperature


def render_upload_tab():
    """Render Upload & Analyze tab."""
    st.header("📤 Upload & Analyze")

    # Introduction
    st.markdown("""
    **Welcome!** This is where you load your CI/CD build data for analysis.

    CI/CD (Continuous Integration/Continuous Deployment) pipelines automatically build, test,
    and deploy your code. This tool analyzes the history of those builds to find problems.
    """)

    with st.expander("📖 What data format do I need?", expanded=False):
        st.markdown("""
        Your CSV file should contain build records with columns like:

        | Column | Description | Example |
        |--------|-------------|---------|
        | `tr_build_id` | Unique build ID | 12345 |
        | `gh_project_name` | Project name | my-app |
        | `tr_status` | Build result | passed, failed, errored |
        | `tr_duration` | How long it took (seconds) | 245 |
        | `gh_build_started_at` | When it started | 2024-01-15 10:30:00 |

        **Don't have data?** Click "Load Sample Data" to try with example data!
        """)

    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Upload your CI/CD build data (CSV file)",
            type=["csv"],
            help="Upload a CSV file with your build history. See the expandable section above for format details.",
        )

    with col2:
        st.markdown("**Or try with sample data:**")
        use_sample = st.button(
            "📊 Load Sample Data",
            use_container_width=True,
            help="Load 10,000 sample builds from real open-source projects to explore the tool.",
        )
        # Download sample data button
        sample_path = Path("data/sample/travistorrent_10k.csv")
        if sample_path.exists():
            with open(sample_path, "rb") as f:
                st.download_button(
                    "⬇️ Download Sample CSV",
                    data=f,
                    file_name="travistorrent_10k.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="Download the sample dataset to explore locally or use in other tools.",
                )

    # Handle data loading
    if use_sample or uploaded_file:
        with st.spinner("Loading and analyzing data... This may take a few seconds."):
            analyzer = ProcessAnalyzer()

            if use_sample:
                sample_path = Path("data/sample/travistorrent_10k.csv")
                if sample_path.exists():
                    analyzer.load_data(sample_path)
                else:
                    st.error(f"Sample file not found: {sample_path}")
                    return
            else:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
                    f.write(uploaded_file.getvalue())
                    temp_path = Path(f.name)
                analyzer.load_data(temp_path)

            # Run analysis
            result = analyzer.analyze()

            # Store in session state
            st.session_state.analysis_result = result
            st.session_state.analyzer = analyzer

            # Auto-generate DFG visualization
            dfg_path = Path("outputs/figures/dfg_streamlit.png")
            dfg_path.parent.mkdir(parents=True, exist_ok=True)
            analyzer.generate_dfg(dfg_path)
            st.session_state.dfg_path = dfg_path

            st.success(f"✅ Successfully analyzed {result.n_builds:,} builds from {result.n_projects} projects!")
            st.info("💡 **Next step:** Check the **Metrics** tab for detailed insights, or ask the **Agent** a question.")

    # Display analysis summary if available
    if st.session_state.analysis_result:
        result = st.session_state.analysis_result

        st.markdown("---")
        st.subheader("📈 Analysis Summary")

        st.markdown("Here's a quick overview of your CI/CD health:")

        # KPI row with explanations
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Builds",
                f"{result.n_builds:,}",
                help="The total number of CI/CD builds analyzed.",
            )
        with col2:
            st.metric(
                "Projects",
                result.n_projects,
                help="Number of different projects/repositories in the data.",
            )
        with col3:
            st.metric(
                "Success Rate",
                f"{result.overall_success_rate:.1%}",
                help="Percentage of builds that passed successfully. Higher is better!",
            )
        with col4:
            st.metric(
                "Median Duration",
                f"{result.median_duration_seconds:.0f}s",
                help="The typical build time. Half of builds are faster, half are slower.",
            )

        # Date range
        if result.date_range_start and result.date_range_end:
            st.caption(
                f"📅 Data covers: {result.date_range_start.strftime('%Y-%m-%d')} to "
                f"{result.date_range_end.strftime('%Y-%m-%d')}"
            )

        # Status distribution
        if result.status_counts:
            st.subheader("Build Status Distribution")
            st.markdown("This shows how many builds ended in each state:")

            with st.expander("What do these statuses mean?"):
                st.markdown("""
                - **passed**: Build completed successfully ✅
                - **failed**: Build failed (usually test failures) ❌
                - **errored**: Build crashed or had infrastructure issues ⚠️
                - **canceled**: Build was manually stopped 🛑
                """)

            status_df = pd.DataFrame(
                list(result.status_counts.items()), columns=["Status", "Count"]
            )
            st.bar_chart(status_df.set_index("Status"))


def render_metrics_tab():
    """Render Metrics Dashboard tab."""
    st.header("📊 Metrics Dashboard")

    if st.session_state.analysis_result is None:
        st.info("👆 **Start here:** Go to the 'Upload & Analyze' tab first to load your data.")
        st.markdown("""
        Once you've loaded data, this tab will show you:
        - Key performance indicators (KPIs)
        - Project-by-project breakdown
        - Problem areas that need attention
        - Process flow visualization
        """)
        return

    result = st.session_state.analysis_result

    st.markdown("This dashboard shows key metrics about your CI/CD pipeline health.")

    # DFG Visualization - at the top for visual impact
    st.subheader("🔄 Process Flow Visualization (DFG)")

    with st.expander("ℹ️ What is a Directly-Follows Graph (DFG)?", expanded=False):
        st.markdown("""
        A **Directly-Follows Graph (DFG)** is a process mining visualization that shows how builds transition between states:

        - **Nodes (circles)** = Build statuses (passed, failed, errored, canceled)
        - **Arrows** = Transitions from one state to the next
        - **Numbers on arrows** = How often each transition happens

        **How to read it:**
        - Thick arrows = frequent transitions (more builds follow this path)
        - `passed → passed` = stable builds, good!
        - `failed → passed` = recovery from failures
        - `failed → failed` = repeated failures (needs investigation)

        **What to look for:**
        - High `passed → passed` count indicates pipeline stability
        - Many `failed → failed` suggests persistent issues
        - `errored` states often indicate infrastructure problems
        """)

    # Show DFG if already generated
    if st.session_state.dfg_path and st.session_state.dfg_path.exists():
        st.image(str(st.session_state.dfg_path), caption="Directly-Follows Graph: Build state transitions in your CI/CD pipeline")
    else:
        # Offer to generate if not yet created
        if st.button("🎨 Generate Process Flow Diagram", help="Creates a visual diagram of build state transitions", key="dfg_top"):
            if st.session_state.analyzer:
                with st.spinner("Generating visualization..."):
                    dfg_path = Path("outputs/figures/dfg_streamlit.png")
                    dfg_path.parent.mkdir(parents=True, exist_ok=True)
                    st.session_state.analyzer.generate_dfg(dfg_path)
                    st.session_state.dfg_path = dfg_path
                    st.rerun()

    # Regenerate button
    if st.session_state.dfg_path:
        if st.button("🔄 Regenerate DFG", help="Generate a fresh visualization", key="dfg_regen_top"):
            if st.session_state.analyzer:
                with st.spinner("Regenerating..."):
                    st.session_state.analyzer.generate_dfg(st.session_state.dfg_path)
                    st.rerun()

    st.markdown("---")

    # KPI cards with explanations
    st.subheader("🎯 Key Performance Indicators")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Success Rate",
            f"{result.overall_success_rate:.1%}",
            help="Percentage of builds that passed. Target: >80%",
        )
        if result.overall_success_rate < 0.8:
            st.caption("⚠️ Below target")
        else:
            st.caption("✅ Healthy")

    with col2:
        st.metric(
            "Failure Rate",
            f"{result.overall_failure_rate:.1%}",
            help="Percentage of builds that failed tests. Target: <15%",
        )
        if result.overall_failure_rate > 0.15:
            st.caption("⚠️ High failures")
        else:
            st.caption("✅ Acceptable")

    with col3:
        st.metric(
            "P90 Duration",
            f"{result.p90_duration_seconds:.0f}s",
            help="90% of builds complete within this time. Shows worst-case performance.",
        )

    with col4:
        bottleneck_count = len(result.bottlenecks) if result.bottlenecks else 0
        st.metric(
            "Bottlenecks",
            bottleneck_count,
            help="Number of slow transitions detected in your pipeline.",
        )
        if bottleneck_count > 0:
            st.caption("⚠️ Needs attention")
        else:
            st.caption("✅ No issues")

    st.markdown("---")

    # Two columns: Projects/Bottlenecks and Risks
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏗️ Project Metrics")
        st.markdown("Performance breakdown by project. Click column headers to sort.")

        if result.project_metrics:
            projects_data = []
            for p in result.project_metrics:
                projects_data.append({
                    "Project": p.project[:40],
                    "Builds": p.n_builds,
                    "Success": f"{p.success_rate:.0%}",
                    "Failure": f"{p.failure_rate:.0%}",
                    "Median (s)": f"{p.median_duration_seconds:.0f}",
                })
            st.dataframe(pd.DataFrame(projects_data), use_container_width=True)
        else:
            st.info("No project metrics available.")

        st.subheader("🐌 Bottlenecks")
        st.markdown("Slow transitions in your pipeline that delay builds:")

        with st.expander("What is a bottleneck?"):
            st.markdown("""
            A **bottleneck** is a step in your CI/CD process that takes much longer than average.

            For example, if most builds take 2 minutes, but some projects consistently take 10 minutes,
            that's a bottleneck worth investigating.
            """)

        if result.bottlenecks:
            for b in result.bottlenecks[:5]:
                st.error(f"**{b.transition}**: {b.avg_wait_seconds:.0f}s avg ({b.frequency} builds)")
        else:
            st.success("✅ No significant bottlenecks detected.")

    with col2:
        st.subheader("⚠️ Projects at Risk")
        st.markdown("Projects with >40% failure+error rate need immediate attention:")

        if result.projects_at_risk:
            for project in result.projects_at_risk:
                st.warning(f"🔴 **{project}**")
            st.markdown("💡 *Tip: Ask the Agent about these projects for recommendations.*")
        else:
            st.success("✅ No projects at critical risk level. Great job!")


def render_agent_tab(model_key: str, temperature: float):
    """Render Agent Analysis tab."""
    st.header("🤖 Agent Analysis")

    if st.session_state.analysis_result is None:
        st.info("👆 **Start here:** Go to the 'Upload & Analyze' tab first to load your data.")
        st.markdown("""
        The AI Agent can:
        - Answer specific questions about your CI/CD data
        - Identify problems and their root causes
        - Provide actionable recommendations
        - Generate comprehensive analysis reports
        """)
        return

    result = st.session_state.analysis_result

    # Introduction
    st.markdown("""
    The **AI Agent** uses large language models (LLMs) to analyze your CI/CD data and provide insights.
    It can understand your questions in plain English and investigate the data to find answers.
    """)

    with st.expander("💡 How does the Agent work?"):
        st.markdown("""
        The Agent uses a technique called **ReAct** (Reason + Act):

        1. **Reads your question** and understands what you want to know
        2. **Calls tools** to analyze different aspects of the data:
           - Summary statistics tool
           - Bottleneck analysis tool
           - Failure pattern tool
           - Project comparison tool
        3. **Synthesizes the results** into a coherent answer
        4. **Provides recommendations** based on what it found

        This is more powerful than simple search because the Agent can reason about the data
        and combine information from multiple sources.
        """)

    st.markdown("---")

    # Model info
    st.markdown(f"**Current model:** `{model_key}` | **Temperature:** {temperature}")

    # All OpenAI models support tools, so no check needed

    st.markdown("---")

    # Question input
    st.subheader("🔍 Ask a Question")

    st.markdown("Type any question about your CI/CD data. Here are some examples:")

    example_questions = [
        "Which projects have the highest failure rates?",
        "What are the main bottlenecks in our pipeline?",
        "Why might project X be failing so often?",
        "What recommendations do you have to improve our CI/CD?",
        "Compare the performance of the top 5 projects",
    ]

    with st.expander("📝 Example questions you can ask"):
        for q in example_questions:
            st.markdown(f"- {q}")

    question = st.text_area(
        "Your question:",
        placeholder="e.g., Which projects have the highest failure rates and why?",
        height=100,
        help="Ask anything about your CI/CD data in plain English.",
    )

    col1, col2 = st.columns(2)

    with col1:
        investigate_btn = st.button(
            "🔍 Investigate Question",
            use_container_width=True,
            help="Analyze your specific question using AI",
        )
    with col2:
        full_analysis_btn = st.button(
            "📋 Run Full Analysis",
            use_container_width=True,
            help="Get a comprehensive analysis of all your CI/CD data (takes longer)",
        )

    # Cost warning
    st.caption("💰 Each query costs approximately $0.001 - $0.01 depending on the response length.")

    # Handle agent actions
    if investigate_btn:
        if not question:
            st.warning("Please enter a question first!")
        else:
            with st.spinner("🤖 Agent is investigating your question... This usually takes 5-15 seconds."):
                agent = DevFlowAgent(model_key=model_key, temperature=temperature)

                with Timer() as timer:
                    response = agent.investigate(result, question)

                # Estimate cost
                input_tokens = len(result.to_llm_context()) // 4 + len(question) // 4
                output_tokens = len(response) // 4
                cost = compute_cost(model_key, input_tokens, output_tokens)

                # Save to run history for Evaluation tab
                import datetime
                st.session_state.run_history.append({
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "type": "Question",
                    "question": question,
                    "model": model_key,
                    "temperature": temperature,
                    "latency_ms": timer.elapsed_ms,
                    "cost_usd": cost,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "response": response,
                })

                st.markdown("### 📝 Agent Response")
                st.markdown(response)

                st.caption(f"⏱️ Completed in {timer.elapsed_ms/1000:.1f} seconds | 💰 Estimated cost: ${cost:.4f}")

    if full_analysis_btn:
        with st.spinner("🤖 Agent is performing comprehensive analysis... This may take 30-60 seconds."):
            agent = DevFlowAgent(model_key=model_key, temperature=temperature)

            with Timer() as timer:
                response = agent.analyze(result)

            # Estimate cost
            input_tokens = len(result.to_llm_context()) // 4
            output_tokens = len(response) // 4
            cost = compute_cost(model_key, input_tokens, output_tokens)

            # Save to run history for Evaluation tab
            import datetime
            st.session_state.run_history.append({
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "Full Analysis",
                "question": "Comprehensive CI/CD analysis",
                "model": model_key,
                "temperature": temperature,
                "latency_ms": timer.elapsed_ms,
                "cost_usd": cost,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "response": response,
            })

            st.markdown("### 📝 Full Analysis Report")
            st.markdown(response)

            st.caption(f"⏱️ Completed in {timer.elapsed_ms/1000:.1f} seconds | 💰 Estimated cost: ${cost:.4f}")


def render_evaluation_tab():
    """Render Evaluation Results tab."""
    st.header("📈 Evaluation & Experiments")

    st.markdown("""
    Track and compare your Agent analyses. Every time you run a query in the **Agent** tab,
    the results are logged here so you can compare performance across different models and settings.
    """)

    # Session Run History - the main feature now
    st.subheader("📊 Session Run History")

    if not st.session_state.run_history:
        st.info("""
        📭 **No runs yet this session.**

        Go to the **Agent** tab and ask some questions! Each analysis will be tracked here
        so you can compare:
        - **Latency** - Which model responds faster?
        - **Cost** - Which model is cheaper?
        - **Quality** - Compare responses side-by-side
        """)

        st.markdown("### 💡 Try this:")
        st.markdown("""
        1. Go to **Agent** tab
        2. Ask: "Which projects have the highest failure rates?"
        3. Come back here to see your run logged
        4. Change the model in the sidebar and ask again
        5. Compare the results!
        """)
    else:
        # Summary metrics
        total_runs = len(st.session_state.run_history)
        total_cost = sum(r["cost_usd"] for r in st.session_state.run_history)
        avg_latency = sum(r["latency_ms"] for r in st.session_state.run_history) / total_runs

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Runs", total_runs)
        col2.metric("Total Cost", f"${total_cost:.4f}")
        col3.metric("Avg Latency", f"{avg_latency/1000:.1f}s")

        st.markdown("---")

        # Run history table
        st.markdown("### Run Details")

        # Create DataFrame for display (with preview)
        display_data = []
        export_data = []
        for i, run in enumerate(reversed(st.session_state.run_history)):
            question = run["question"]
            response = run["response"]

            # Display version (truncated)
            display_data.append({
                "#": total_runs - i,
                "Time": run["timestamp"],
                "Type": run["type"],
                "Question": question[:50] + "..." if len(question) > 50 else question,
                "Model": run["model"],
                "Temp": run["temperature"],
                "Latency": f"{run['latency_ms']/1000:.1f}s",
                "Cost": f"${run['cost_usd']:.4f}",
                "Response Preview": response[:100] + "..." if len(response) > 100 else response,
            })

            # Export version (full data)
            export_data.append({
                "#": total_runs - i,
                "Time": run["timestamp"],
                "Type": run["type"],
                "Question": question,
                "Model": run["model"],
                "Temperature": run["temperature"],
                "Latency (s)": run["latency_ms"] / 1000,
                "Cost (USD)": run["cost_usd"],
                "Input Tokens": run["input_tokens"],
                "Output Tokens": run["output_tokens"],
                "Response": response,
            })

        st.dataframe(pd.DataFrame(display_data), use_container_width=True, hide_index=True)

        # Download as CSV button (full data)
        export_df = pd.DataFrame(export_data)
        csv_data = export_df.to_csv(index=False)
        st.download_button(
            "⬇️ Download Run History as CSV",
            data=csv_data,
            file_name="devflow_run_history.csv",
            mime="text/csv",
            help="Download the full run history including complete responses.",
        )

        # Model comparison if multiple models used
        models_used = set(r["model"] for r in st.session_state.run_history)
        if len(models_used) > 1:
            st.markdown("### 🔄 Model Comparison")
            st.markdown("You've used multiple models! Here's how they compare:")

            for model in models_used:
                model_runs = [r for r in st.session_state.run_history if r["model"] == model]
                avg_latency = sum(r["latency_ms"] for r in model_runs) / len(model_runs)
                avg_cost = sum(r["cost_usd"] for r in model_runs) / len(model_runs)

                col1, col2, col3 = st.columns([2, 1, 1])
                col1.markdown(f"**{model}**")
                col2.metric("Avg Latency", f"{avg_latency/1000:.1f}s", label_visibility="collapsed")
                col3.metric("Avg Cost", f"${avg_cost:.4f}", label_visibility="collapsed")

        # Clear history button
        st.markdown("---")
        if st.button("🗑️ Clear Run History", help="Remove all tracked runs from this session"):
            st.session_state.run_history = []
            st.rerun()

    # Advanced: MLflow section (collapsed by default)
    st.markdown("---")
    with st.expander("🔬 Advanced: MLflow Experiment Tracking"):
        st.markdown("""
        For **persistent** experiment tracking across sessions, use MLflow via Python code.
        The session history above is cleared when you close the app.

        **To persist experiments:**
        """)

        st.code("""
from src.evaluation import ExperimentTracker, Timer, compute_cost
from src.agent import DevFlowAgent

tracker = ExperimentTracker('my-experiment')

with tracker.start_run('run-name'):
    tracker.log_params({'model': 'gpt-4o-mini', 'temperature': 0.3})

    agent = DevFlowAgent(model_key='gpt-4o-mini')
    with Timer() as timer:
        response = agent.analyze(result)

    tracker.log_metrics({
        'latency_ms': timer.elapsed_ms,
        'cost_usd': compute_cost('gpt-4o-mini', 1000, 500)
    })
        """, language="python")

        st.markdown("""
        **View MLflow dashboard:**
        ```bash
        mlflow ui --port 5000
        ```
        """)


def main():
    """Main application."""
    st.title("🔄 DevFlow Analyzer")
    st.markdown(
        "**Analyze your CI/CD build data** with process mining and AI-powered insights."
    )

    # Quick start guide for new users
    with st.expander("🚀 New here? Start with this guide!", expanded=False):
        st.markdown("""
        ### How to use DevFlow Analyzer

        1. **Upload & Analyze** (Tab 1)
           - Upload your CI/CD build data as a CSV file
           - Or click "Load Sample Data" to try with example data

        2. **Metrics** (Tab 2)
           - View key performance indicators
           - See which projects need attention
           - Generate process flow visualizations

        3. **Agent** (Tab 3)
           - Ask questions in plain English
           - Get AI-powered insights and recommendations

        4. **Evaluation** (Tab 4)
           - Track experiments over time
           - Compare different analyses

        **Tip:** Start with the sample data to explore all features!
        """)

    # Sidebar
    model_key, temperature = render_sidebar()

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📤 Upload & Analyze",
        "📊 Metrics",
        "🤖 Agent",
        "📈 Evaluation",
    ])

    with tab1:
        render_upload_tab()

    with tab2:
        render_metrics_tab()

    with tab3:
        render_agent_tab(model_key, temperature)

    with tab4:
        render_evaluation_tab()


if __name__ == "__main__":
    main()
