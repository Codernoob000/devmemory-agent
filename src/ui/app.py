import streamlit as st
import pandas as pd
import json

# 1. GLOBAL PAGE CONFIGURATION & DARK CANVAS MATRIX
st.set_page_config(
    page_title="DevMemory Agent Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Style Injector: Fixes fonts, card borders, and telemetry layouts cleanly
st.markdown("""
    <style>
        /* Base Canvas & Font Weights */
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');
        html, body, [data-testid="stAppViewContainer"] {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        
        /* Monospace Code Editor Styling for Raw Ingestion */
        div[data-testid="stTextArea"] textarea {
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 13px !important;
            background-color: #0d1117 !important;
            color: #4af626 !important;
            border: 1px solid #30363d !important;
            border-radius: 6px !important;
        }
        
        /* Metric Card Containers Visual Polishing */
        div[data-testid="stMetricContainer"] {
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
            padding: 15px 20px !important;
            border-radius: 8px !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        div[data-testid="stMetricValue"] {
            font-size: 28px !important;
            font-weight: 600 !important;
        }
        
        /* Clean Headers and Section Dividers */
        h1, h2, h3 {
            font-weight: 500 !important;
            letter-spacing: -0.5px !important;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🛠️ SIDEBAR CONTROL DECK
# ==========================================
with st.sidebar:
    st.markdown("### 🎛️ Control Deck")
    st.markdown("<p style='color:#8b949e; font-size:12px; margin-top:-10px;'>Active System Architecture Configuration</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Visual Status Pill
    st.markdown("""
        <div style='background-color: rgba(46, 160, 67, 0.15); border: 1px solid #2ea043; padding: 10px; border-radius: 6px; margin-bottom: 20px;'>
            <span style='color: #3fb950; font-weight: 600;'>● Status:</span> Active & Online
        </div>
    """, unsafe_allow_html=True)
    
    # Grouping Config Properties inside a container
    with st.container():
        st.markdown("**Core Pipelines & Layers:**")
        st.caption("🚦 Traffic Routing:")
        st.markdown("`cascadeflow (Active)`")
        
        st.caption("⚡ Fast Filter Engine:")
        st.markdown("`Qwen-2.5-32B (Groq)`")
        
        st.caption("🧠 Flagship Reasoning Layer:")
        st.markdown("`LLaMA-3.3-70B (Groq)`")
        
        st.caption("💾 Long-Term Memory Asset:")
        st.markdown("`Vectorize Hindsight`")
        
        st.caption("📢 Target Dispatch Hook:")
        st.markdown("`#devmemory-alerts`")

# ==========================================
# 🚀 MAIN DASHBOARD BODY FRAME
# ==========================================
st.title("🧠 DevMemory Agent")
st.markdown("<p style='color:#8b949e; font-size:16px; margin-top:-15px;'>Real-Time SRE Log Ingestion & Persistent Memory Synthesis Pipeline</p>", unsafe_allow_html=True)
st.markdown("---")

# Split Pane Layout Strategy
col_left, col_right = st.columns([1, 1.1], gap="large")

# ------------------------------------------
# LEFT PANE: INGESTION PIPELINE
# ------------------------------------------
with col_left:
    st.markdown("### 📥 Ingest Live Production Log")
    
    # Interactive scenario picker
    selected_scenario = st.selectbox(
        "Quick Demo: Load realistic crash signature:",
        [
            "-- Select Scenario --", 
            "Scenario 1: sqlalchemy.exc.TimeoutError", 
            "Scenario 2: redis.exceptions.ResponseError", 
            "Scenario 3: RuntimeError", 
            "Scenario 4: org.apache.kafka.clients.consumer.CommitFailedException...", 
            "Scenario 5: django.db.utils.OperationalError"
        ]
    )
    
    # Script input payload container
    log_input = st.text_area(
        "Paste Raw Exception Payload / Server Logs:",
        height=280,
        placeholder="2026-06-27 22:18:06 FATAL: Enter infrastructure dump sequence..."
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    trigger_pipeline = st.button("🚀 Trigger Ingest & Escalation Pipeline", use_container_width=True)

# ------------------------------------------
# RIGHT PANE: SYNTHESIZED REPORT OUTPUT
# ------------------------------------------
with col_right:
    st.markdown("### 📄 SRE Post-Mortem Report")
    
    # UI Sandbox State Machine Emulation
    if trigger_pipeline and "-- Select Scenario --" not in selected_scenario:
        # Green System Banner Execution State Tracker
        st.success("Pipeline executed cleanly! Incident escalated and report generated.")
        
        # Hardcoded beautiful output rendering to match your working metrics engine structure
        st.markdown("""
        ## Incident Post-Mortem
        
        ### 🔍 Incident Summary
        The current incident involves a **sqlalchemy.exc.TimeoutError** indicating that the PostgreSQL database connection pool exhaustion has been reached, causing a complete system traffic timeout block.
        
        ### 🛠️ Root Cause Analysis
        The root cause stems from unclosed cursors and context leaks within asynchronous worker threads. Connections are assigned but never explicitly returned to the QueuePool context layer.
        
        ### 🧠 Matching Historical Incident
        * **Incident ID:** `outage-session-001`
        * **Historical Date:** 2025-11-12
        * **Semantic Similarity Vector:** `0.53` (High Correlation)
        * **Past Resolution Track:** Ensuring all asynchronous data transactions utilize proper connection closures or Python context managers.
        """)
    else:
        # Elegant initial structural layout placeholder frame
        st.info("Ingest a log track on the left pane to synthesize the dynamic Markdown post-mortem document.")

st.markdown("---")

# ==========================================
# 📊 TELEMETRY DATA PANEL (BOTTOM DRAWER)
# ==========================================
st.markdown("### 📊 Live Decision Audit Trail & Cumulative Telemetry")

# Metrics Container Row
m1, m2, m3, m4 = st.columns(4)
m1.metric(label="Total Logs Processed", value="19 runs", delta="+3 tonight")
m2.metric(label="Escalation Rate Target", value="68.4%", delta="Optimized via Gate")
m3.metric(label="Cumulative Financial Savings", value="$0.0079", delta="+$0.00137 saved", delta_color="inverse")
m4.metric(label="Slack Alerts Dispatched", value="13 notifications", delta="+2 dispatched")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("**Detailed Historic Audits Matrix:**")

# Recreating your mock database logs directly into an enterprise-safe structured layout grid
mock_audit_data = {
    "Timestamp": ["2026-06-27 22:18:06", "2026-06-27 22:15:56", "2026-06-27 22:11:24", "2026-06-27 22:07:05", "2026-06-27 21:57:57"],
    "Severity": ["CRITICAL", "CRITICAL", "CRITICAL", "CRITICAL", "HIGH"],
    "Error Type": ["Timeout", "Connection Error", "Timeout", "Timeout", "None"],
    "Escalated": ["Yes 🚀", "Yes 🚀", "Yes 🚀", "Yes 🚀", "No 🔕"],
    "Models Used": ["qwen3-32b, llama-3.3-70b", "qwen3-32b, llama-3.3-70b", "qwen3-32b, llama-3.3-70b", "qwen3-32b, llama-3.3-70b", "qwen3-32b (Filtered Space)"],
    "Latency (ms)": [2371.1, 1984.2, 2157.3, 1806.4, 3101.0],
    "Savings ($)": [0.000418, 0.000344, 0.000433, 0.000375, 0.000671],
    "Hindsight Match": ["Yes 🧠", "Yes 🧠", "Yes 🧠", "Yes 🧠", "No ❌"],
    "Slack Dispatched": ["Yes ✅", "Yes ✅", "Yes ✅", "Yes ✅", "No ❌"]
}

df = pd.DataFrame(mock_audit_data)
st.dataframe(df, use_container_width=True, hide_index=True)