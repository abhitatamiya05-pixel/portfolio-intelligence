import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from src.data_loader import load_data, apply_chart_theme, fmt_currency, portfolio_kpis, STATUS_COLORS, RISK_COLORS, DEPT_COLORS

st.set_page_config(
    page_title="Portfolio Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    .kpi-card { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px;
                padding: 1rem 1.2rem; margin-bottom: 0.5rem; }
    .kpi-value { font-size: 1.9rem; font-weight: 700; color: #1E293B; line-height: 1.1; }
    .kpi-label { font-size: 0.78rem; color: #64748B; text-transform: uppercase;
                 letter-spacing: 0.06em; margin-top: 0.2rem; }
    .kpi-delta { font-size: 0.82rem; margin-top: 0.25rem; font-weight: 500; }
    .section-header { font-size: 1.05rem; font-weight: 600; color: #1E293B;
                      border-bottom: 2px solid #E2E8F0; padding-bottom: 0.4rem;
                      margin: 1.2rem 0 0.8rem; }
    .alert-row { background: #FEF3C7; border-left: 4px solid #F59E0B;
                 padding: 0.6rem 0.9rem; border-radius: 0 6px 6px 0; margin-bottom: 0.4rem; }
    .alert-critical { background: #FEE2E2; border-left-color: #EF4444; }
    div[data-testid="stSidebarContent"] { background: #F8FAFC; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def get_data():
    return load_data()


with st.spinner("Initializing portfolio data..."):
    data = get_data()

projects = data["projects"]
kpis = portfolio_kpis(projects)

# ── Header ─────────────────────────────────────────────────────────────────────
col_title, col_date = st.columns([3, 1])
with col_title:
    st.markdown("## Portfolio Risk & Resource Intelligence")
    st.caption("Decision-support dashboard for PMO leadership · Data as of April 25, 2025")
with col_date:
    at_risk = kpis["at_risk_count"]
    critical = kpis["critical_count"]
    if critical > 0:
        st.error(f"⚠️  **{critical}** critical projects require immediate attention", icon=None)
    elif at_risk > 0:
        st.warning(f"⚡ **{at_risk}** projects at risk", icon=None)
    else:
        st.success("Portfolio health: Good", icon=None)

# ── KPI Row ────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

bv_color = "#EF4444" if kpis["budget_variance_pct"] > 10 else "#F59E0B" if kpis["budget_variance_pct"] > 5 else "#10B981"
health_color = "#10B981" if kpis["avg_health"] >= 70 else "#F59E0B" if kpis["avg_health"] >= 55 else "#EF4444"

with k1:
    st.markdown(f"""<div class="kpi-card">
    <div class="kpi-value">{fmt_currency(kpis["total_portfolio_value"])}</div>
    <div class="kpi-label">Total Portfolio Value</div>
    <div class="kpi-delta" style="color:#64748B;">Forecast: {fmt_currency(kpis["total_forecast"])}</div>
    </div>""", unsafe_allow_html=True)

with k2:
    st.markdown(f"""<div class="kpi-card">
    <div class="kpi-value">{kpis["project_count"]}</div>
    <div class="kpi-label">Total Projects</div>
    <div class="kpi-delta" style="color:#6366F1;">{kpis["completed_count"]} completed · {kpis["active_count"]} active</div>
    </div>""", unsafe_allow_html=True)

with k3:
    st.markdown(f"""<div class="kpi-card">
    <div class="kpi-value" style="color:#EF4444;">{kpis["at_risk_count"]}</div>
    <div class="kpi-label">Projects At Risk / Off Track</div>
    <div class="kpi-delta" style="color:#EF4444;">{kpis["at_risk_pct"]}% of portfolio · {kpis["critical_count"]} critical</div>
    </div>""", unsafe_allow_html=True)

with k4:
    sign = "+" if kpis["budget_variance_pct"] > 0 else ""
    st.markdown(f"""<div class="kpi-card">
    <div class="kpi-value" style="color:{bv_color};">{sign}{kpis["budget_variance_pct"]}%</div>
    <div class="kpi-label">Portfolio Budget Variance</div>
    <div class="kpi-delta" style="color:{bv_color};">{fmt_currency(kpis["total_forecast"] - kpis["total_portfolio_value"])} overrun</div>
    </div>""", unsafe_allow_html=True)

with k5:
    st.markdown(f"""<div class="kpi-card">
    <div class="kpi-value" style="color:{health_color};">{kpis["avg_health"]}</div>
    <div class="kpi-label">Avg Portfolio Health Index</div>
    <div class="kpi-delta" style="color:#64748B;">Avg completion: {kpis["avg_completion"]}%</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ── Charts Row 1 ───────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([1.2, 1.2, 1.6])

with c1:
    st.markdown('<div class="section-header">Project Status Distribution</div>', unsafe_allow_html=True)
    status_counts = projects["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    fig = px.pie(
        status_counts, names="status", values="count",
        color="status", color_discrete_map=STATUS_COLORS,
        hole=0.55,
    )
    fig.update_traces(textposition="outside", textinfo="percent+label", showlegend=False)
    fig.update_layout(
        plot_bgcolor="#FFF", paper_bgcolor="#FFF",
        margin=dict(l=10, r=10, t=10, b=10), height=280,
        annotations=[dict(text=f"<b>{len(projects)}</b><br>Projects", x=0.5, y=0.5,
                          font_size=14, showarrow=False)],
    )
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.markdown('<div class="section-header">Risk Level Distribution</div>', unsafe_allow_html=True)
    risk_counts = projects["risk_level"].value_counts().reindex(
        ["Critical", "High", "Medium", "Low"], fill_value=0
    ).reset_index()
    risk_counts.columns = ["risk_level", "count"]
    fig2 = px.bar(
        risk_counts, x="count", y="risk_level", orientation="h",
        color="risk_level", color_discrete_map=RISK_COLORS,
        text="count",
    )
    fig2.update_traces(textposition="outside", showlegend=False)
    apply_chart_theme(fig2, height=280)
    fig2.update_layout(margin=dict(l=10, r=30, t=10, b=10), xaxis_title="", yaxis_title="")
    st.plotly_chart(fig2, use_container_width=True)

with c3:
    st.markdown('<div class="section-header">Portfolio Value by Department & Status</div>', unsafe_allow_html=True)
    dept_status = projects.groupby(["department", "status"])["estimated_budget"].sum().reset_index()
    fig3 = px.bar(
        dept_status, x="department", y="estimated_budget", color="status",
        color_discrete_map=STATUS_COLORS, barmode="stack",
        labels={"estimated_budget": "Budget ($)", "department": ""},
    )
    fig3.update_yaxes(tickformat="$.0s")
    apply_chart_theme(fig3, height=280)
    fig3.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig3, use_container_width=True)

# ── Charts Row 2 ───────────────────────────────────────────────────────────────
c4, c5 = st.columns([1.6, 1.4])

with c4:
    st.markdown('<div class="section-header">Strategic Value vs Risk — Portfolio Bubble Map</div>', unsafe_allow_html=True)
    active_p = projects[projects["status"] != "Completed"].copy()
    fig4 = px.scatter(
        active_p,
        x="risk_score", y="business_value_score",
        size="estimated_budget", color="department",
        color_discrete_map=DEPT_COLORS,
        hover_name="project_name",
        hover_data={"status": True, "estimated_budget": ":$,.0f", "risk_score": ":.0f",
                    "business_value_score": True, "project_manager": True},
        size_max=28,
        labels={"risk_score": "Risk Score (0–100)", "business_value_score": "Business Value (0–100)"},
    )
    fig4.add_vline(x=50, line_dash="dot", line_color="#94A3B8", annotation_text="Risk threshold")
    fig4.add_hline(y=50, line_dash="dot", line_color="#94A3B8", annotation_text="Value threshold")
    apply_chart_theme(fig4, height=340)
    st.plotly_chart(fig4, use_container_width=True)

with c5:
    st.markdown('<div class="section-header">Top 10 Projects Needing Attention</div>', unsafe_allow_html=True)
    top_risk = (
        projects[projects["status"].isin(["At Risk", "Off Track", "On Hold"])]
        .sort_values(["risk_score", "business_value_score"], ascending=[False, False])
        .head(10)[["project_name", "department", "status", "risk_score", "budget_variance_pct", "schedule_variance_days"]]
    )
    top_risk = top_risk.rename(columns={
        "project_name": "Project", "department": "Dept", "status": "Status",
        "risk_score": "Risk", "budget_variance_pct": "Budget Δ%", "schedule_variance_days": "Slip (days)",
    })

    st.dataframe(top_risk, use_container_width=True, height=340)

# ── Sidebar navigation hint ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Navigation")
    st.markdown("""
Use the pages in the sidebar to explore:
- **Portfolio Overview** — full project inventory & timelines
- **Risk Intelligence** — ML risk scoring & analysis
- **Resource Intelligence** — utilization & bottlenecks
- **Scenario Planning** — what-if analysis & optimization
- **Executive Briefing** — auto-generated narrative & recommendations
""")
    st.markdown("---")
    st.markdown("**Portfolio last refreshed**  \nApril 25, 2025")
    st.markdown("**Total projects tracked**  \n" + str(len(projects)))
    st.markdown("**Reporting currency**  \nUSD")
