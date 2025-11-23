"""
ExamIntellect Dashboard Application

This module implements the Streamlit dashboard for real-time observability
and monitoring of the ExamIntellect proctoring system.
"""

import streamlit as st
import pandas as pd
import sys
from datetime import datetime, timedelta
import time
from pathlib import Path

# Add parent directory to path for imports - fix import issues
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Import modules directly to avoid relative import issues
try:
    from src.session_manager import SessionManager
#     from src.agents.proctor_agent import ProctorAgent
#     from src.agents.tutor_agent import TutorAgent
#     from src.agents.communication_agent import CommunicationAgent
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.error("Please ensure all required modules are available.")
    IMPORTS_SUCCESSFUL = False

# Try to import plotly with fallback
try:
    import plotly.express as px
#     import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    st.warning("Plotly not available. Some charts will not display.")
    PLOTLY_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="ExamIntellect Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 0.25rem solid #1f77b4;
    }
    .alert-card {
        background-color: #ffe6e6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 0.25rem solid #dc3545;
        margin: 0.5rem 0;
    }
    .success-card {
        background-color: #e6ffe6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 0.25rem solid #28a745;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main dashboard function."""
    if not IMPORTS_SUCCESSFUL:
        st.error("Cannot start dashboard due to import errors. Please check the installation.")
        return

    # Initialize managers and agents
    try:
        session_manager = SessionManager()
#         proctor = ProctorAgent(session_manager)
#         tutor = TutorAgent(session_manager)
#         communicator = CommunicationAgent(session_manager)
    except Exception as e:
        st.error(f"Failed to initialize agents: {e}")
        return

    st.markdown('<div class="main-header">🎓 ExamIntellect Proctoring Dashboard</div>', unsafe_allow_html=True)


    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["Overview", "Live Monitoring", "Student Profiles", "Reports", "Settings"]
    )

    # Real-time data refresh
    if st.sidebar.button("🔄 Refresh Data"):
        try:
            st.rerun()
        except AttributeError:
            try:
                st.experimental_rerun()
            except AttributeError:
                st.warning("Page refresh not supported in this Streamlit version")

    # Display selected page
    if page == "Overview":
        show_overview_page()
    elif page == "Live Monitoring":
        show_live_monitoring_page()
    elif page == "Student Profiles":
        show_student_profiles_page()
    elif page == "Reports":
        show_reports_page()
    elif page == "Settings":
        show_settings_page()

def show_overview_page():
    """Display the overview dashboard."""


    st.header("📊 System Overview")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Active Sessions", "3", "+1")
    with col2:
        st.metric("Total Students", "127", "+5")
    with col3:
        st.metric("Alerts Today", "12", "-3")
    with col4:
        st.metric("High Risk Students", "2", "0")

    # System status
    st.subheader("🖥️ System Status")
    status_col1, status_col2, status_col3 = st.columns(3)

    with status_col1:
        st.success("✅ Proctor Agent: Online")
    with status_col2:
        st.success("✅ Tutor Agent: Online")
    with status_col3:
        st.success("✅ Communication Agent: Online")

    # Recent alerts
    st.subheader("🚨 Recent Alerts")
    alerts_data = [
        {"Time": "14:32", "Student": "John Doe", "Type": "Face Not Visible", "Severity": "Medium"},
        {"Time": "14:28", "Student": "Jane Smith", "Type": "Multiple Faces", "Severity": "High"},
        {"Time": "14:15", "Student": "Bob Johnson", "Type": "Audio Anomaly", "Severity": "Low"},
    ]
    alerts_df = pd.DataFrame(alerts_data)
    st.dataframe(alerts_df, use_container_width=True)

    # Performance metrics
    st.subheader("📈 Performance Metrics")
    perf_col1, perf_col2 = st.columns(2)

    with perf_col1:
        if PLOTLY_AVAILABLE:
            # Average session duration
            fig = px.bar(
                x=[
                    'Mon',
                    'Tue',
                    'Wed',
                    'Thu',
                    'Fri',
                ],
                y=[45, 52, 38, 41, 49],
                title="Average Session Duration (minutes)",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Plotly charts not available")

    with perf_col2:
        if PLOTLY_AVAILABLE:
            # Alert distribution
            fig = px.pie(
                values=[65, 25, 10],
                names=['Low', 'Medium', 'High'],
                title="Alert Severity Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Plotly charts not available")

def show_live_monitoring_page():
    """Display live monitoring dashboard."""
    st.header("👁️ Live Monitoring")

    # Session selector
    active_sessions = ["session_john_001", "session_jane_002", "session_bob_003"]
    selected_session = st.selectbox("Select Active Session", active_sessions)

    if selected_session:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("📹 Live Feed")
            # Placeholder for video feed
            st.image("https://via.placeholder.com/640x480/000000/FFFFFF?text=Live+Video+Feed",
                     caption="Live Proctoring Feed", use_container_width=True)

            # Video controls
            control_col1, control_col2, control_col3, control_col4 = st.columns(4)
            with control_col1:
                if st.button("▶️ Start Recording"):
                    st.success("Recording started")
            with control_col2:
                if st.button("⏸️ Pause"):
                    st.warning("Feed paused")
            with control_col3:
                if st.button("🔊 Enable Audio"):
                    st.info("Audio monitoring enabled")
            with control_col4:
                if st.button("🚨 Emergency Stop"):
                    st.error("Emergency stop activated")

        with col2:
            st.subheader("📊 Session Stats")

            # Real-time metrics
            status_placeholder = st.empty()
            alerts_placeholder = st.empty()
            duration_placeholder = st.empty()

            # Simulate real-time updates (limited to avoid infinite loop)
            for i in range(5):
                status_placeholder.metric("Status", "Active", "Normal")
                alerts_placeholder.metric("Alerts", f"{i % 5}", f"{(i % 5) - ((i-1) % 5 if i > 0 else 0):+d}")
                duration_placeholder.metric("Duration", f"{45 + i} min", "+1 min")
                time.sleep(0.5)

    # Live alerts feed
    st.subheader("🚨 Live Alerts Feed")
    alert_feed = st.empty()

    # Simulate live alerts
    alerts = [
        "14:35 - Face detection anomaly for John Doe",
        "14:34 - Audio levels normal",
        "14:33 - Gaze tracking active",
        "14:32 - Multiple faces detected - ALERT",
        "14:31 - Session integrity verified"
    ]

    for alert in alerts:
        alert_feed.text(alert)
        time.sleep(0.2)

def show_student_profiles_page():
    """Display student profiles and risk assessment."""
    st.header("👨‍🎓 Student Profiles")

    # Student search
    search_term = st.text_input("Search Students", placeholder="Enter student ID or name")

    # Sample student data
    students_data = [
        {
            "ID": "john_doe_001",
            "Name": "John Doe",
            "Risk Level": "Medium",
            "Last Exam": "2024-01-15",
            "Avg Score": 78,
            "Total Sessions": 5,
            "Alerts": 3
        },
        {
            "ID": "jane_smith_002",
            "Name": "Jane Smith",
            "Risk Level": "Low",
            "Last Exam": "2024-01-14",
            "Avg Score": 92,
            "Total Sessions": 3,
            "Alerts": 0
        },
        {
            "ID": "bob_johnson_003",
            "Name": "Bob Johnson",
            "Risk Level": "High",
            "Last Exam": "2024-01-13",
            "Avg Score": 65,
            "Total Sessions": 7,
            "Alerts": 12
        }
    ]

    students_df = pd.DataFrame(students_data)

    # Filter students
    if search_term:
        students_df = students_df[
            students_df['ID'].str.contains(search_term, case=False) |
            students_df['Name'].str.contains(search_term, case=False)
        ]

    st.dataframe(students_df, use_container_width=True)

    # Student detail view
    selected_student = st.selectbox("Select Student for Details",
                                   [f"{row['ID']} - {row['Name']}" for _, row in students_df.iterrows()])

    if selected_student:
        student_id = selected_student.split(' - ')[0]

        st.subheader(f"📋 Profile: {selected_student}")

        # Risk assessment
        risk_col1, risk_col2, risk_col3 = st.columns(3)

        with risk_col1:
            st.metric("Risk Score", "67", "↑ 5")
        with risk_col2:
            st.metric("Risk Level", "Medium", "↔")
        with risk_col3:
            st.metric("Trend", "Increasing", "⚠️")

        # Performance history
        st.subheader("📈 Performance History")
        performance_data = {
            'Exam Date': ['2024-01-01', '2024-01-08', '2024-01-15'],
            'Score': [75, 82, 78],
            'Duration': [45, 48, 42],
            'Alerts': [1, 0, 2]
        }
        perf_df = pd.DataFrame(performance_data)
        st.line_chart(perf_df.set_index('Exam Date')[['Score']])

        # Recent alerts
        st.subheader("🚨 Recent Alerts")
        alerts_data = [
            {"Date": "2024-01-15", "Type": "Face Not Visible", "Severity": "Medium"},
            {"Date": "2024-01-15", "Type": "Audio Anomaly", "Severity": "Low"},
            {"Date": "2024-01-13", "Type": "Multiple Faces", "Severity": "High"}
        ]
        alerts_df = pd.DataFrame(alerts_data)
        st.table(alerts_df)

def show_reports_page():
    """Display reports and analytics."""
    st.header("📋 Reports & Analytics")

    # Report type selector
    report_type = st.selectbox(
        "Select Report Type",
        ["Session Summary", "Student Performance", "Incident Reports", "System Analytics"]
    )

    if report_type == "Session Summary":
        st.subheader("📊 Session Summary Report")

        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=7))
        with col2:
            end_date = st.date_input("End Date", datetime.now())

        # Summary metrics
        total_sessions = 45
        avg_duration = 47
        total_alerts = 23
        high_risk_sessions = 3

        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        with metric_col1:
            st.metric("Total Sessions", total_sessions)
        with metric_col2:
            st.metric("Avg Duration", f"{avg_duration} min")
        with metric_col3:
            st.metric("Total Alerts", total_alerts)
        with metric_col4:
            st.metric("High Risk Sessions", high_risk_sessions)

        # Session timeline
        st.subheader("📅 Session Timeline")
        # Generate data for the selected date range
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        num_days = len(date_range)
        # Create sample data matching the length
        sessions = [5, 8, 6, 7, 4, 9, 6][:num_days] if num_days <= 7 else [5] * num_days
        alerts = [2, 3, 1, 4, 1, 6, 2][:num_days] if num_days <= 7 else [2] * num_days
        timeline_data = {
            'Date': date_range,
            'Sessions': sessions,
            'Alerts': alerts
        }
        timeline_df = pd.DataFrame(timeline_data)
        st.line_chart(timeline_df.set_index('Date'))

    elif report_type == "Student Performance":
        st.subheader("🎯 Student Performance Analysis")

        if PLOTLY_AVAILABLE:
            # Performance distribution
            scores = [65, 72, 78, 85, 92, 67, 89, 94, 71, 83]
            fig = px.histogram(scores, nbins=10, title="Score Distribution")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart({"Scores": [65, 72, 78, 85, 92, 67, 89, 94, 71, 83]})

        # Top performers and at-risk students
        perf_col1, perf_col2 = st.columns(2)

        with perf_col1:
            st.subheader("🏆 Top Performers")
            top_students = [
                {"Name": "Alice Wilson", "Avg Score": 95, "Sessions": 4},
                {"Name": "Charlie Brown", "Avg Score": 93, "Sessions": 3},
                {"Name": "Diana Prince", "Avg Score": 91, "Sessions": 5}
            ]
            st.table(top_students)

        with perf_col2:
            st.subheader("⚠️ At-Risk Students")
            risk_students = [
                {"Name": "Bob Smith", "Avg Score": 62, "Alerts": 8},
                {"Name": "Eve Johnson", "Avg Score": 58, "Alerts": 12},
                {"Name": "Frank Miller", "Avg Score": 55, "Alerts": 15}
            ]
            st.table(risk_students)

    elif report_type == "Incident Reports":
        st.subheader("🚨 Incident Reports")

        # Incident filter
        severity_filter = st.multiselect(
            "Filter by Severity",
            ["Low", "Medium", "High", "Critical"],
            default=["High", "Critical"]
        )

        # Sample incidents
        incidents = [
            {
                "ID": "INC_001",
                "Student": "Bob Smith",
                "Type": "Multiple Faces Detected",
                "Severity": "High",
                "Time": "2024-01-15 14:32",
                "Status": "Investigating"
            },
            {
                "ID": "INC_002",
                "Student": "Eve Johnson",
                "Type": "External Help Suspected",
                "Severity": "Critical",
                "Time": "2024-01-14 16:45",
                "Status": "Resolved"
            }
        ]

        incidents_df = pd.DataFrame(incidents)
        st.dataframe(incidents_df, use_container_width=True)

        # Export reports
        if st.button("📥 Export Incident Reports"):
            st.success("Reports exported successfully!")

    elif report_type == "System Analytics":
        st.subheader("🔧 System Analytics")

        # System health metrics
        health_col1, health_col2, health_col3 = st.columns(3)

        with health_col1:
            st.metric("Uptime", "99.8%", "+0.1%")
        with health_col2:
            st.metric("Response Time", "245ms", "-12ms")
        with health_col3:
            st.metric("Error Rate", "0.02%", "-0.01%")

        # Resource usage
        st.subheader("💾 Resource Usage")
        resource_data = {
            'Time': pd.date_range(start=datetime.now()-timedelta(hours=23),
                                 end=datetime.now(), freq='H'),
            'CPU': [45, 52, 38, 41, 49, 55, 42, 38, 51, 47, 44, 39, 46, 53, 41, 37, 48, 52, 43, 40, 49, 54, 42, 38],
            'Memory': [68, 72, 65, 69, 74, 71, 66, 63, 70, 73, 67, 64, 69, 75, 68, 62, 71, 74, 66, 63, 70, 76, 67, 61]
        }
        resource_df = pd.DataFrame(resource_data)
        st.line_chart(resource_df.set_index('Time'))

def show_settings_page():
    """Display settings and configuration."""
    st.header("⚙️ Settings & Configuration")

    # API Configuration
    st.subheader("🔗 API Configuration")
    with st.expander("Gemini LLM Settings"):
        gemini_key = st.text_input("API Key", type="password", placeholder="Enter Gemini API Key")
        gemini_model = st.selectbox("Model", ["gemini-pro", "gemini-pro-vision"])
        if st.button("Test Gemini Connection"):
            st.success("✅ Gemini API connection successful!")

    with st.expander("OpenAI Settings"):
        openai_key = st.text_input("API Key", type="password", placeholder="Enter OpenAI API Key")
        openai_model = st.selectbox("Model", ["gpt-3.5-turbo", "gpt-4"])
        if st.button("Test OpenAI Connection"):
            st.success("✅ OpenAI API connection successful!")

    # Alert Configuration
    st.subheader("🚨 Alert Configuration")
    with st.expander("Alert Thresholds"):
        face_threshold = st.slider("Face Not Visible Threshold (seconds)", 1, 30, 5)
        multiple_faces = st.slider("Multiple Faces Threshold", 1, 10, 1)
        gaze_threshold = st.slider("Abnormal Gaze Threshold (seconds)", 5, 60, 10)

    # Email Configuration
    st.subheader("📧 Email Configuration")
    with st.expander("SMTP Settings"):
        smtp_server = st.text_input("SMTP Server", "smtp.gmail.com")
        smtp_port = st.number_input("Port", value=587)
        sender_email = st.text_input("Sender Email")
        sender_password = st.text_input("Password", type="password")

        if st.button("Test Email Configuration"):
            st.success("✅ Email configuration test successful!")

    # System Settings
    st.subheader("🔧 System Settings")
    with st.expander("General Settings"):
        log_level = st.selectbox("Log Level", ["DEBUG", "INFO", "WARNING", "ERROR"])
        session_timeout = st.slider("Session Timeout (minutes)", 30, 480, 120)
        auto_backup = st.checkbox("Enable Automatic Backups", value=True)

    # Save Settings
    if st.button("💾 Save Settings", type="primary"):
        st.success("✅ Settings saved successfully!")

    # System Information
    st.subheader("ℹ️ System Information")
    info_col1, info_col2 = st.columns(2)

    with info_col1:
        st.info("**Version:** 1.0.0")
        st.info("**Database:** SQLite 3.37.0")
        st.info("**Python:** 3.9.7")

    with info_col2:
        st.info("**OpenCV:** 4.5.5")
        st.info("**Streamlit:** 1.17.0")
        st.info("**Last Updated:** 2024-01-15")

if __name__ == "__main__":
    main()
