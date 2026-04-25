import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from src.data_loader import load_data, apply_chart_theme, fmt_currency, portfolio_kpis, STATUS_COLORS, RISK_COLORS, DEPT_COLORS
from src.resource_analyzer import compute_utilization, get_overloaded_resources
from src.recommendations import generate_recommendations, generate_executive_narrative

st.set_page_config(page_title="Executive Briefing", page_icon="📋", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .exec-section { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px;
                    padding: 1.2rem 1.4rem; margin-bottom: 1rem; }
    .exec-section h4 { font-size: 0.95rem; color: #2563EB; text-transform: uppercase;
                       letter-spacing: 0.06em; margin: 0 0 0.7rem 0; font-weight: 700; }
    .rec-card { border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.6rem; }
    .rec-critical { background: #FEE2E2; border-left: 4px solid #EF4444; }
    .rec-high { background: #FFF7ED; border-left: 4px solid #F97316; }
    .rec-medium { background: #FEF3C7; border-left: 4px solid #F59E0B; }
    .rec-title { font-weight: 700; font-size: 0.95rem; color: #1E293B; margin-bottom: 0.3rem; }
    .rec-detail { font-size: 0.85rem; color: #475569; margin-bottom: 0.4rem; }
    .rec-action { font-size: 0.85rem; color: #1E293B; background: #FFFFFF80;
                  padding: 0.3rem 0.6rem; border-radius: 5px; margin-top: 0.3rem; }
    .rec-metric { display:inline-block; background: #FFFFFF; border-radius: 12px;
                  padding: 2px 8px; font-size: 0.78rem; font-weight: 600; color: #64748B;
                  margin-top: 0.3rem; }
    .health-indicator { text-align: center; padding: 1.5rem; }
    .health-number { font-size: 4rem; font-weight: 800; line-height: 1; }
    .health-label { font-size: 0.85rem; color: #64748B; text-transform: uppercase;
                    letter-spacing: 0.08em; margin-top: 0.4rem; }
    .kpi-inline { display: flex; gap: 1.5rem; flex-wrap: wrap; margin: 0.5rem 0; }
    .kpi-inline-item { text-align: center; }
    .kpi-inline-val { font-size: 1.4rem; font-weight: 700; color: #1E293B; }
    .kpi-inline-lbl { font-size: 0.72rem; color: #64748B; text-transform: uppercase; }
    .section-header { font-size: 1.05rem; font-weight: 600; color: #1E293B;
                      border-bottom: 2px solid #E2E8F0; padding-bottom: 0.4rem;
                      margin: 1.2rem 0 0.8rem; }
</style>
""", unsafe_allow_html=True)

data = load_data()
projects = data["projects"]
resources = data["resources"]
allocations = data["allocations"]
kpis = portfolio_kpis(projects)

@st.cache_data(show_spinner=False)
def get_analytics(n: int):
    util = compute_utilization(allocations, resources)
    overloaded = get_overloaded_resources(util)
    narrative = generate_executive_narrative(projects, util, kpis)
    recs = generate_recommendations(projects, resources, util, overloaded)
    return util, overloaded, narrative, recs

util, overloaded, narrative, recs = get_analytics(len(projects) + len(allocations))

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("## Executive Portfolio Briefing")
st.caption("Auto-generated · Portfolio intelligence summary for PMO leadership · April 25, 2025")
st.markdown("---")

# ── Row 1: Health gauge + Key narratives ──────────────────────────────────────
col_health, col_narrative = st.columns([1, 2.5])

with col_health:
    h = kpis["avg_health"]
    health_color = "#10B981" if h >= 70 else "#F59E0B" if h >= 55 else "#EF4444"
    health_label_text = "HEALTHY" if h >= 70 else "AT RISK" if h >= 55 else "CRITICAL"

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=h,
        number={"font": {"size": 40, "color": health_color}, "suffix": ""},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94A3B8"},
            "bar": {"color": health_color, "thickness": 0.28},
            "bgcolor": "#F1F5F9",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40], "color": "#FEE2E2"},
                {"range": [40, 60], "color": "#FEF3C7"},
                {"range": [60, 80], "color": "#DCFCE7"},
                {"range": [80, 100], "color": "#D1FAE5"},
            ],
            "threshold": {"line": {"color": health_color, "width": 4}, "thickness": 0.85, "value": h},
        },
        title={"text": f"<b>{health_label_text}</b>", "font": {"size": 14, "color": health_color}},
    ))
    fig_gauge.update_layout(
        plot_bgcolor="#FFF", paper_bgcolor="#FFF",
        margin=dict(l=20, r=20, t=30, b=10), height=240,
        font=dict(family="Inter", color="#1E293B"),
    )
    st.plotly_chart(fig_gauge, use_container_width=True)
    st.markdown(f"<div style='text-align:center;font-size:0.78rem;color:#64748B;'>Portfolio Health Index<br>{kpis['project_count']} projects · ${kpis['total_portfolio_value']/1e6:.0f}M</div>",
                unsafe_allow_html=True)

with col_narrative:
    st.markdown('<div class="section-header">Portfolio Health Summary</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="exec-section"><h4>Portfolio Overview</h4>{narrative["portfolio_health"]}</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="exec-section"><h4>Risk Overview</h4>{narrative["risk_summary"]}</div>',
                unsafe_allow_html=True)

# ── Row 2: Additional narratives ───────────────────────────────────────────────
col_n3, col_n4 = st.columns(2)
with col_n3:
    st.markdown(f'<div class="exec-section"><h4>Resource Overview</h4>{narrative["resource_summary"]}</div>',
                unsafe_allow_html=True)
with col_n4:
    st.markdown(f'<div class="exec-section"><h4>Strategic Alignment</h4>{narrative["strategic_alignment"]}</div>',
                unsafe_allow_html=True)

# ── Key numbers ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-header">Portfolio Snapshot — Key Numbers</div>', unsafe_allow_html=True)

k1, k2, k3, k4, k5, k6, k7 = st.columns(7)
snap_metrics = [
    (str(kpis["project_count"]), "Total Projects"),
    (str(kpis["active_count"]), "Active"),
    (str(kpis["completed_count"]), "Completed"),
    (str(kpis["at_risk_count"]), "At Risk / Off Track"),
    (str(kpis["critical_count"]), "Critical Risk"),
    (f"{kpis['avg_completion']}%", "Avg Completion"),
    (f"{kpis['budget_variance_pct']:+.1f}%", "Budget Variance"),
]
for col, (val, lbl) in zip([k1, k2, k3, k4, k5, k6, k7], snap_metrics):
    col.metric(lbl, val)

# ── Recommendations ────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-header">Recommended Actions — Prioritized for Leadership Review</div>',
            unsafe_allow_html=True)

priority_style = {"Critical": "rec-critical", "High": "rec-high", "Medium": "rec-medium", "Low": "rec-medium"}
priority_badge_color = {"Critical": "#B91C1C", "High": "#C2410C", "Medium": "#92400E", "Low": "#1E40AF"}

col_recs_a, col_recs_b = st.columns(2)
left_recs = recs[:len(recs)//2 + len(recs) % 2]
right_recs = recs[len(recs)//2 + len(recs) % 2:]

for rec_col, rec_list in [(col_recs_a, left_recs), (col_recs_b, right_recs)]:
    with rec_col:
        for rec in rec_list:
            p_class = priority_style.get(rec["priority"], "rec-medium")
            p_color = priority_badge_color.get(rec["priority"], "#64748B")
            st.markdown(f"""
            <div class="rec-card {p_class}">
                <div class="rec-title">{rec["icon"]} {rec["title"]}</div>
                <div style="display:inline-block;background:{p_color};color:white;border-radius:10px;
                            padding:1px 8px;font-size:0.72rem;font-weight:700;margin-bottom:0.4rem;">
                    {rec["priority"].upper()} · {rec["category"]}
                </div>
                <div class="rec-detail">{rec["detail"]}</div>
                <div class="rec-action">→ <b>Recommended Action:</b> {rec["action"]}</div>
                <div class="rec-metric">{rec["metric"]}</div>
            </div>
            """, unsafe_allow_html=True)

# ── Supporting Charts ──────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-header">Supporting Analysis</div>', unsafe_allow_html=True)

c_a, c_b, c_c = st.columns(3)

with c_a:
    st.markdown("**Project Manager Workload**")
    pm_load = (
        projects[projects["status"].isin(["On Track", "At Risk", "Off Track"])]
        .groupby("project_manager")
        .agg(active_projects=("project_id", "count"), avg_risk=("risk_score", "mean"))
        .reset_index()
        .sort_values("active_projects", ascending=True)
    )
    fig_pm = px.bar(
        pm_load, x="active_projects", y="project_manager", orientation="h",
        color="avg_risk",
        color_continuous_scale=["#10B981", "#F59E0B", "#EF4444"],
        color_continuous_midpoint=40,
        text="active_projects",
        labels={"active_projects": "Active Projects", "project_manager": "", "avg_risk": "Avg Risk"},
    )
    fig_pm.update_traces(textposition="outside")
    fig_pm.add_vline(x=5, line_dash="dot", line_color="#F59E0B", annotation_text="Recommended max")
    apply_chart_theme(fig_pm, height=420)
    fig_pm.update_layout(margin=dict(l=100, r=40, t=30, b=20), coloraxis_showscale=False)
    st.plotly_chart(fig_pm, use_container_width=True)

with c_b:
    st.markdown("**Budget Overrun Exposure by Department**")
    dept_budget = projects.groupby("department").agg(
        planned=("estimated_budget", "sum"),
        forecast=("forecast_at_completion", "sum"),
    ).reset_index()
    dept_budget["overrun"] = dept_budget["forecast"] - dept_budget["planned"]
    dept_budget["overrun_pct"] = (dept_budget["overrun"] / dept_budget["planned"] * 100).round(1)
    dept_budget = dept_budget.sort_values("overrun_pct", ascending=True)

    fig_overrun = go.Figure()
    fig_overrun.add_trace(go.Bar(
        y=dept_budget["department"],
        x=dept_budget["overrun_pct"],
        orientation="h",
        marker_color=[
            "#EF4444" if v > 15 else "#F59E0B" if v > 8 else "#10B981"
            for v in dept_budget["overrun_pct"]
        ],
        text=dept_budget["overrun_pct"].map("{:+.1f}%".format),
        textposition="outside",
    ))
    fig_overrun.add_vline(x=0, line_color="#1E293B", line_width=1)
    fig_overrun.add_vline(x=10, line_dash="dot", line_color="#F59E0B")
    fig_overrun.update_layout(xaxis_title="Budget Variance %", yaxis_title="")
    apply_chart_theme(fig_overrun, height=280)
    st.plotly_chart(fig_overrun, use_container_width=True)

    st.markdown("**Strategic Priority Mix**")
    prio_counts = projects["strategic_priority"].value_counts().sort_index().reset_index()
    prio_counts.columns = ["Priority", "Count"]
    prio_counts["label"] = prio_counts["Priority"].map({
        1: "1-Low", 2: "2-Below Avg", 3: "3-Medium", 4: "4-High", 5: "5-Critical"
    })
    fig_prio = px.bar(prio_counts, x="label", y="Count",
                      color="Priority",
                      color_continuous_scale=["#DBEAFE", "#2563EB", "#1D4ED8"],
                      labels={"label": "", "Count": "Projects"})
    fig_prio.update_coloraxes(showscale=False)
    apply_chart_theme(fig_prio, height=200)
    fig_prio.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_prio, use_container_width=True)

with c_c:
    st.markdown("**Risk Level by Department (Stacked)**")
    risk_dept = projects.groupby(["department", "risk_level"])["project_id"].count().reset_index()
    risk_dept.columns = ["department", "risk_level", "count"]
    risk_dept["risk_level"] = pd.Categorical(
        risk_dept["risk_level"], categories=["Low", "Medium", "High", "Critical"], ordered=True
    )
    risk_dept = risk_dept.sort_values("risk_level")

    fig_rd = px.bar(
        risk_dept, x="department", y="count", color="risk_level",
        color_discrete_map=RISK_COLORS, barmode="stack",
        labels={"count": "Projects", "department": "", "risk_level": "Risk"},
        category_orders={"risk_level": ["Low", "Medium", "High", "Critical"]},
    )
    apply_chart_theme(fig_rd, height=280)
    st.plotly_chart(fig_rd, use_container_width=True)

    st.markdown("**Completion vs Health Correlation**")
    active_sample = projects[projects["status"] != "Completed"].sample(min(80, len(projects)), random_state=42)
    fig_ch = px.scatter(
        active_sample, x="completion_pct", y="health_index",
        color="department", color_discrete_map=DEPT_COLORS,
        size="estimated_budget", size_max=18,

        labels={"completion_pct": "Completion %", "health_index": "Health Index"},
    )
    apply_chart_theme(fig_ch, height=240)
    fig_ch.update_layout(showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_ch, use_container_width=True)

# ── Key Decisions Footer ────────────────────────────────────────────────────────
st.markdown("---")
critical_recs = [r for r in recs if r["priority"] == "Critical"]
high_recs = [r for r in recs if r["priority"] == "High"]

if critical_recs or high_recs:
    st.markdown("### Key Decisions Required from Leadership")
    decision_items = critical_recs + high_recs
    for i, rec in enumerate(decision_items, 1):
        st.markdown(f"**{i}. {rec['title']}**  \n{rec['action']}")

st.markdown("---")
st.caption(
    f"Portfolio Intelligence Platform · Reporting Period: April 2025 · "
    f"{kpis['project_count']} Projects · ${kpis['total_portfolio_value']/1e6:.0f}M Total Portfolio Value · "
    f"Auto-generated analysis using ML risk scoring and rule-based heuristics"
)
