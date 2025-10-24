"""Main Streamlit dashboard application."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False
    st = None


@dataclass
class DashboardState:
    """Global dashboard state."""
    
    current_suite: Optional[str] = None
    current_run: Optional[str] = None
    refresh_interval: int = 2000  # milliseconds
    theme: str = "light"


class DashboardApp:
    """Main dashboard application."""
    
    def __init__(self, workspace_path: Optional[Path] = None):
        """Initialize dashboard.
        
        Args:
            workspace_path: Path to AgentUnit workspace directory
        """
        if not HAS_STREAMLIT:
            raise ImportError(
                "streamlit is required for the dashboard. "
                "Install it with: pip install streamlit"
            )
        
        self.workspace_path = workspace_path or Path.cwd()
        self.state = DashboardState()
        
    def run(self):
        """Run the dashboard application."""
        st.set_page_config(
            page_title="AgentUnit Dashboard",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Apply custom CSS
        self._apply_styles()
        
        # Sidebar navigation
        page = self._render_sidebar()
        
        # Main content
        if page == "Suite Editor":
            self._render_suite_editor()
        elif page == "Run Monitor":
            self._render_run_monitor()
        elif page == "Trace Viewer":
            self._render_trace_viewer()
        elif page == "Reports":
            self._render_reports()
        elif page == "Settings":
            self._render_settings()
    
    def _apply_styles(self):
        """Apply custom CSS styles."""
        st.markdown("""
            <style>
            .metric-card {
                background-color: #f0f2f6;
                padding: 20px;
                border-radius: 10px;
                margin: 10px 0;
            }
            .success-metric {
                color: #28a745;
                font-size: 24px;
                font-weight: bold;
            }
            .failure-metric {
                color: #dc3545;
                font-size: 24px;
                font-weight: bold;
            }
            .trace-step {
                border-left: 3px solid #4CAF50;
                padding-left: 15px;
                margin: 10px 0;
            }
            </style>
        """, unsafe_allow_html=True)
    
    def _render_sidebar(self) -> str:
        """Render sidebar navigation.
        
        Returns:
            Selected page name
        """
        with st.sidebar:
            st.title("AgentUnit Dashboard")
            st.markdown("---")
            
            page = st.radio(
                "Navigation",
                ["Suite Editor", "Run Monitor", "Trace Viewer", "Reports", "Settings"],
                label_visibility="collapsed"
            )
            
            st.markdown("---")
            
            # Workspace info
            st.subheader("Workspace")
            st.text(str(self.workspace_path))
            
            # Quick stats
            st.subheader("Quick Stats")
            suites = self._get_suites()
            runs = self._get_runs()
            st.metric("Total Suites", len(suites))
            st.metric("Total Runs", len(runs))
            
            return page
    
    def _render_suite_editor(self):
        """Render suite editor page."""
        st.header("Suite Editor")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Suites")
            suites = self._get_suites()
            
            # Create new suite
            with st.expander("Create New Suite"):
                suite_name = st.text_input("Suite Name")
                if st.button("Create"):
                    self._create_suite(suite_name)
                    st.success(f"Created suite: {suite_name}")
                    st.rerun()
            
            # List existing suites
            for suite in suites:
                if st.button(suite, key=f"suite_{suite}"):
                    self.state.current_suite = suite
        
        with col2:
            if self.state.current_suite:
                st.subheader(f"Editing: {self.state.current_suite}")
                self._render_suite_form(self.state.current_suite)
            else:
                st.info("Select a suite to edit or create a new one")
    
    def _render_suite_form(self, suite_name: str):
        """Render suite editing form.
        
        Args:
            suite_name: Name of the suite to edit
        """
        suite_data = self._load_suite(suite_name)
        
        # Basic info
        st.text_input("Description", value=suite_data.get("description", ""))
        
        # Adapter configuration
        st.subheader("Adapter Configuration")
        adapter_type = st.selectbox(
            "Adapter Type",
            ["openai", "anthropic", "custom"],
            index=0 if suite_data.get("adapter", {}).get("type") == "openai" else 1
        )
        
        if adapter_type == "openai":
            model = st.text_input("Model", value=suite_data.get("adapter", {}).get("model", "gpt-4"))
            temperature = st.slider("Temperature", 0.0, 2.0, 
                                  suite_data.get("adapter", {}).get("temperature", 0.7))
        
        # Metrics
        st.subheader("Metrics")
        available_metrics = [
            "ExactMatch", "SemanticSimilarity", "JSONValidation",
            "ToolCallAccuracy", "LatencyMetric"
        ]
        selected_metrics = st.multiselect(
            "Enabled Metrics",
            available_metrics,
            default=suite_data.get("metrics", [])
        )
        
        # Dataset
        st.subheader("Dataset")
        dataset_source = st.radio("Dataset Source", ["Upload JSON", "Use Existing", "Generate"])
        
        if dataset_source == "Upload JSON":
            uploaded_file = st.file_uploader("Choose dataset file", type=["json"])
            if uploaded_file:
                st.json(json.load(uploaded_file))
        
        # Save button
        if st.button("Save Suite"):
            self._save_suite(suite_name, {
                "description": "",
                "adapter": {"type": adapter_type},
                "metrics": selected_metrics
            })
            st.success("Suite saved!")
    
    def _render_run_monitor(self):
        """Render run monitor page."""
        st.header("Run Monitor")
        
        # Controls
        col1, col2, col3 = st.columns(3)
        with col1:
            suite = st.selectbox("Suite", self._get_suites())
        with col2:
            if st.button("Start Run"):
                st.info("Starting run...")
        with col3:
            auto_refresh = st.checkbox("Auto Refresh", value=True)
        
        # Recent runs
        st.subheader("Recent Runs")
        runs = self._get_runs()
        
        for run in runs[:10]:
            with st.expander(f"Run {run['id']} - {run['status']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Cases", run.get("total", 0))
                with col2:
                    st.metric("Passed", run.get("passed", 0))
                with col3:
                    st.metric("Failed", run.get("failed", 0))
                
                # Progress bar
                if run.get("total", 0) > 0:
                    progress = run.get("passed", 0) / run.get("total", 1)
                    st.progress(progress)
                
                if st.button("View Details", key=f"view_{run['id']}"):
                    self.state.current_run = run['id']
                    st.switch_page("Trace Viewer")
    
    def _render_trace_viewer(self):
        """Render trace viewer page."""
        st.header("Trace Viewer")
        
        if self.state.current_run:
            run_data = self._load_run(self.state.current_run)
            
            # Run summary
            st.subheader("Run Summary")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Cases", run_data.get("total", 0))
            with col2:
                st.metric("Passed", run_data.get("passed", 0))
            with col3:
                st.metric("Failed", run_data.get("failed", 0))
            with col4:
                st.metric("Avg Latency", f"{run_data.get('avg_latency', 0):.2f}s")
            
            # Trace list
            st.subheader("Traces")
            traces = run_data.get("traces", [])
            
            # Filter options
            status_filter = st.multiselect(
                "Filter by status",
                ["passed", "failed", "error"],
                default=["passed", "failed", "error"]
            )
            
            filtered_traces = [t for t in traces if t.get("status") in status_filter]
            
            for trace in filtered_traces:
                status_color = "🟢" if trace.get("status") == "passed" else "🔴"
                with st.expander(f"{status_color} {trace.get('case_id', 'Unknown')}"):
                    self._render_trace_detail(trace)
        else:
            st.info("Select a run from the Run Monitor to view traces")
    
    def _render_trace_detail(self, trace: Dict[str, Any]):
        """Render detailed trace information.
        
        Args:
            trace: Trace data dictionary
        """
        # Input/Output
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Input")
            st.code(trace.get("input", ""), language="json")
        with col2:
            st.subheader("Output")
            st.code(trace.get("output", ""), language="json")
        
        # Tool calls
        if trace.get("tool_calls"):
            st.subheader("Tool Calls")
            for i, call in enumerate(trace["tool_calls"], 1):
                st.markdown(f"""
                <div class="trace-step">
                    <strong>Step {i}:</strong> {call.get('name', 'Unknown')}<br>
                    <code>{json.dumps(call.get('args', {}), indent=2)}</code>
                </div>
                """, unsafe_allow_html=True)
        
        # Metrics
        st.subheader("Metrics")
        for metric_name, metric_value in trace.get("metrics", {}).items():
            col1, col2 = st.columns([2, 1])
            with col1:
                st.text(metric_name)
            with col2:
                if isinstance(metric_value, (int, float)):
                    st.progress(min(metric_value, 1.0))
                else:
                    st.text(str(metric_value))
    
    def _render_reports(self):
        """Render reports page."""
        st.header("Reports")
        
        # Report type selector
        report_type = st.selectbox(
            "Report Type",
            ["Summary Report", "Comparison Report", "Regression Report"]
        )
        
        if report_type == "Summary Report":
            runs = self._get_runs()
            selected_run = st.selectbox("Select Run", [r["id"] for r in runs])
            
            if selected_run:
                run_data = self._load_run(selected_run)
                
                # Summary metrics
                st.subheader("Summary Metrics")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Success Rate", 
                             f"{run_data.get('passed', 0) / max(run_data.get('total', 1), 1) * 100:.1f}%")
                with col2:
                    st.metric("Avg Latency", f"{run_data.get('avg_latency', 0):.2f}s")
                with col3:
                    st.metric("Total Cost", f"${run_data.get('cost', 0):.4f}")
                
                # Metric breakdown
                st.subheader("Metric Breakdown")
                # TODO: Add charts using plotly or altair
                
        elif report_type == "Comparison Report":
            st.info("Select two runs to compare")
            # TODO: Implement comparison UI
            
        elif report_type == "Regression Report":
            st.info("Configure regression detection settings")
            # TODO: Implement regression detection UI
    
    def _render_settings(self):
        """Render settings page."""
        st.header("Settings")
        
        # Dashboard settings
        st.subheader("Dashboard Settings")
        theme = st.selectbox("Theme", ["light", "dark"], 
                           index=0 if self.state.theme == "light" else 1)
        refresh_interval = st.slider("Auto-refresh Interval (ms)", 
                                    1000, 10000, self.state.refresh_interval)
        
        # Workspace settings
        st.subheader("Workspace Settings")
        st.text_input("Workspace Path", value=str(self.workspace_path))
        
        # API keys
        st.subheader("API Keys")
        openai_key = st.text_input("OpenAI API Key", type="password")
        anthropic_key = st.text_input("Anthropic API Key", type="password")
        
        if st.button("Save Settings"):
            self.state.theme = theme
            self.state.refresh_interval = refresh_interval
            st.success("Settings saved!")
    
    # Helper methods
    
    def _get_suites(self) -> List[str]:
        """Get list of available suites."""
        suites_dir = self.workspace_path / "suites"
        if not suites_dir.exists():
            return []
        return [f.stem for f in suites_dir.glob("*.json")]
    
    def _get_runs(self) -> List[Dict[str, Any]]:
        """Get list of recent runs."""
        runs_dir = self.workspace_path / "runs"
        if not runs_dir.exists():
            return []
        
        runs = []
        for run_file in sorted(runs_dir.glob("*.json"), reverse=True)[:20]:
            with open(run_file) as f:
                runs.append(json.load(f))
        return runs
    
    def _create_suite(self, name: str):
        """Create a new suite."""
        suites_dir = self.workspace_path / "suites"
        suites_dir.mkdir(exist_ok=True)
        
        suite_path = suites_dir / f"{name}.json"
        with open(suite_path, 'w') as f:
            json.dump({
                "name": name,
                "description": "",
                "adapter": {},
                "metrics": [],
                "dataset": []
            }, f, indent=2)
    
    def _load_suite(self, name: str) -> Dict[str, Any]:
        """Load suite configuration."""
        suite_path = self.workspace_path / "suites" / f"{name}.json"
        if suite_path.exists():
            with open(suite_path) as f:
                return json.load(f)
        return {}
    
    def _save_suite(self, name: str, data: Dict[str, Any]):
        """Save suite configuration."""
        suite_path = self.workspace_path / "suites" / f"{name}.json"
        with open(suite_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_run(self, run_id: str) -> Dict[str, Any]:
        """Load run data."""
        run_path = self.workspace_path / "runs" / f"{run_id}.json"
        if run_path.exists():
            with open(run_path) as f:
                return json.load(f)
        return {}
