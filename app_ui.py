import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

import os

# --- Configuration ---
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
st.set_page_config(
    page_title="Antigravity | Portfolio Intelligence",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Institutional Look ---
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
    .report-section {
        background-color: #161b22;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #30363d;
        margin-bottom: 20px;
    }
    .causal-chain {
        border-left: 4px solid #58a6ff;
        padding-left: 15px;
        margin-bottom: 15px;
    }
    .risk-high { color: #ff7b72; font-weight: bold; }
    .risk-medium { color: #d29922; font-weight: bold; }
    .risk-low { color: #3fb950; font-weight: bold; }
    h1, h2, h3 { color: #adbac7 !important; }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def fetch_portfolios():
    try:
        response = requests.get(f"{API_BASE_URL}/portfolios")
        return response.json()["portfolios"]
    except:
        return []

def fetch_analysis(portfolio_id):
    response = requests.get(f"{API_BASE_URL}/api/advisor-evaluation/{portfolio_id}")
    return response.json()

# --- Sidebar ---
st.sidebar.title("🎯 Antigravity PM")
st.sidebar.markdown("---")

portfolios = fetch_portfolios()
if not portfolios:
    st.sidebar.error("Backend offline. Start main.py first.")
    st.stop()

portfolio_options = {f"{p['user_name']} - {p['portfolio_id']}": p['portfolio_id'] for p in portfolios}
selected_p_name = st.sidebar.selectbox("Select Portfolio", options=list(portfolio_options.keys()))
portfolio_id = portfolio_options[selected_p_name]

if st.sidebar.button("Generate Intelligence Report"):
    with st.spinner("Executing Causal Reasoning Engine..."):
        st.session_state.report_data = fetch_analysis(portfolio_id)
        st.session_state.last_id = portfolio_id

# --- Main Dashboard ---
if "report_data" not in st.session_state or st.session_state.last_id != portfolio_id:
    st.title("Portfolio Intelligence Terminal")
    st.info("Select a portfolio and click 'Generate Intelligence Report' to begin analysis.")
else:
    data = st.session_state.report_data
    report = data["advisor_report"]
    analysis = data["portfolio_analysis"]
    eval_audit = data["evaluation"]

    # 1. Executive Portfolio Snapshot
    st.markdown(f"# Intelligence Report: {selected_p_name}")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Value", f"₹{analysis['total_current_value']:,.0f}")
    with col2:
        st.metric("Absolute P&L", f"₹{analysis['total_pnl']:,.0f}", f"{analysis['pnl_percent']}%")
    with col3:
        st.metric("Market Sentiment", report['market_sentiment'])
    with col4:
        st.metric("Risk Grade", eval_audit['risk_grade'])
    with col5:
        st.metric("Diversification", f"{analysis['risk_diagnostics']['diversification_score']}/100")

    st.markdown(f"""
    <div class="report-section">
        <h3>Executive Summary</h3>
        <p style="font-size: 1.1em; color: #adbac7;">{report['executive_summary']}</p>
    </div>
    """, unsafe_allow_html=True)

    # 2. Effective Exposure & Look-Through
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Exposure Analytics", "⛓️ Causal Reasoning", "⚠️ Risk & Stress", "🔄 Rebalancing"])

    with tab1:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("Effective Sector Exposure")
            exp_data = analysis["effective_sector_exposure"]
            df_exp = pd.DataFrame(list(exp_data.items()), columns=["Sector", "Weight%"])
            fig = px.pie(df_exp, values="Weight%", names="Sector", hole=0.4, 
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                              font_color="#adbac7", margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.subheader("Major Holdings")
            major = pd.DataFrame(analysis["major_holdings"])
            st.table(major)

        st.subheader("Mutual Fund Look-Through Decomposition")
        lt_df = []
        for mf in analysis["look_through_details"]:
            for sec, weight in mf["decomposed_sectors"].items():
                lt_df.append({"Fund": mf["fund_name"], "Sector": sec, "Contribution%": weight})
        if lt_df:
            st.dataframe(pd.DataFrame(lt_df), use_container_width=True)

    with tab2:
        st.subheader("News → Sector → Holding → Portfolio Causal Chains")
        for chain in report["causal_driver_chains"]:
            st.markdown(f"""
            <div class="causal-chain">
                <p><b>Event:</b> {chain['event']}</p>
                <p><b>Transmission:</b> {chain['macro_variable']} → {chain['sector_impact']}</p>
                <p><b>Affected:</b> {chain['affected_holdings']}</p>
                <p style="color: {'#ff7b72' if chain['estimated_portfolio_impact'] < 0 else '#3fb950'}">
                    <b>Portfolio Impact:</b> {chain['estimated_portfolio_impact']}% (Strength: {chain['strength']})
                </p>
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        st.subheader("Material Risk Diagnostics")
        rd = analysis["risk_diagnostics"]
        r1, r2, r3 = st.columns(3)
        r1.metric("HHI Score", rd["hhi"], rd["hhi_status"])
        r2.metric("Beta Sensitivity", rd["beta_sensitivity"])
        r3.metric("Overlap Risk", rd["overlap_risk"])

        st.markdown("### Stress Test Scenarios")
        st_data = analysis["stress_tests"]
        st_df = pd.DataFrame(st_data)
        fig_st = px.bar(st_df, x="impact_percent", y="scenario", orientation='h',
                        title="Scenario Drawdown Projections",
                        color="impact_percent", color_continuous_scale="RdYlGn")
        fig_st.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#adbac7")
        st.plotly_chart(fig_st, use_container_width=True)

        with st.expander("Vulnerable Holdings Detail"):
            for s in st_data:
                st.write(f"**{s['scenario']}**: {', '.join(s['vulnerable_holdings'])}")

    with tab4:
        st.subheader("Strategic Rebalancing Engine")
        reb_list = report["strategic_rebalancing_actions"]
        if reb_list:
            for action in reb_list:
                with st.container():
                    st.markdown(f"#### {action['action']}")
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"**Allocation Shift:** {action['current_allocation']}% → {action['target_allocation']}%")
                    c2.write(f"**Expected Benefit:** {action['expected_benefit']}")
                    c3.write(f"**Tradeoff:** {action['tradeoff']}")
                    st.info(f"**Reasoning:** {action['reasoning']}")
                    st.markdown("---")
        else:
            st.success("No urgent rebalancing required based on current causal signals.")

    # 8. Reasoning Confidence & Audit
    st.markdown("---")
    st.subheader("Reasoning Audit & Evidence Coverage")
    a1, a2, a3 = st.columns(3)
    a1.metric("Audit Score", f"{eval_audit['score']}/10")
    a2.metric("Confidence", report["confidence_level"])
    a3.metric("Latency", f"{report['latency_ms']}ms")
    
    st.markdown(f"""
    <div style="background-color: #1c2128; padding: 15px; border-radius: 8px;">
        <p><b>Auditor Critique:</b> {eval_audit['critique']}</p>
        <p style="font-size: 0.9em; color: #768390;">Run ID: {report['run_id']} | Method: Groq Llama-3.3-70B</p>
    </div>
    """, unsafe_allow_html=True)

    # Chat Interface at the bottom
    st.markdown("---")
    st.subheader("💬 Ask Advisor Anything")
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about specific holdings, macro risks, or rebalancing logic"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            payload = {"query": prompt, "portfolio_id": portfolio_id}
            response = requests.post(f"{API_BASE_URL}/chat/query", json=payload).json()
            st.markdown(response["answer"])
            if response.get("sources_used"):
                st.caption(f"Sources: {', '.join(response['sources_used'])}")
            st.session_state.messages.append({"role": "assistant", "content": response["answer"]})
