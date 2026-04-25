import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from src.data_loader import load_data, apply_chart_theme, fmt_currency, STATUS_COLORS, DEPT_COLORS, RISK_COLORS

st.set_page_config(page_title="Portfolio Overview", page_icon="📋", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .section-header { font-size: 1.05rem; font-weight: 600; color: #1E293B;
                      border-bottom: 2px solid #E2E8F0; padding-bottom: 0.4rem;
                      margin: 1.2rem 0 0.8rem; }
    .metric-sm { background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px;
                 padding:0.7rem 1rem; text-align:center; }
    .metric-sm .val { font-size:1.4rem; font-weight:700; color:#1E293B; }
    .metric-sm .lbl { font-size:0.72rem; color:#64748B; text-transform:uppercase; }
</style>
""", unsafe_allow_html=True)

data = load_data()
projects = data["projects"]

st.markdown("## Portfolio Overview")
st.caption("Full project inventory, budget performance, and delivery timeline analysis")

# ── Sidebar Filters ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Filters")
    sel_depts = st.multiselect("Department", sorted(projects["department"].unique()), default=[])
    sel_status = st.multiselect("Status", sorted(projects["status"].unique()), default=[])
    sel_phase = st.multiselect("Phase", sorted(projects["phase"].unique()), default=[])
    sel_priority = st.multiselect("Strategic Priority", sorted(projects["strategic_priority"].unique()), default=[])
    sel_size = st.multiselect("Project Size", ["Small", "Medium", "Large", "Very Large"], default=[])
    search = st.text_input("Search project name", placeholder="e.g. Cloud, ERP...")

df = projects.copy()
if sel_depts:
    df = df[df["department"].isin(sel_depts)]
if sel_status:
    df = df[df["status"].isin(sel_status)]
if sel_phase:
    df = df[df["phase"].isin(sel_phase)]
if sel_priority:
    df = df[df["strategic_priority"].isin(sel_priority)]
if sel_size:
    df = df[df["size_category"].isin(sel_size)]
if search:
    df = df[df["project_name"].str.contains(search, case=False, na=False)]

# ── Filtered KPIs ──────────────────────────────────────────────────────────────
m1, m2, m3, m4, m5, m6 = st.columns(6)
metrics = [
    (str(len(df)), "Projects"),
    (fmt_currency(df["estimated_budget"].sum()), "Total Budget"),
    (fmt_currency(df["forecast_at_completion"].sum()), "Forecast at Completion"),
    (f"{df[df['status'].isin(['At Risk','Off Track'])].shape[0]}", "At Risk / Off Track"),
    (f"{df['completion_pct'].mean():.0f}%", "Avg Completion"),
    (f"{df['risk_score'].mean():.0f}/100", "Avg Risk Score"),
]
for col, (val, lbl) in zip([m1, m2, m3, m4, m5, m6], metrics):
    col.markdown(f'<div class="metric-sm"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>',
                 unsafe_allow_html=True)

st.markdown("---")

# ── Budget by Department ────────────────────────────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    st.markdown('<div class="section-header">Budget Performance by Department</div>', unsafe_allow_html=True)
    dept_budget = df.groupby("department").agg(
        Planned=("estimated_budget", "sum"),
        Actual_YTD=("actual_spend_ytd", "sum"),
        Forecast=("forecast_at_completion", "sum"),
    ).reset_index().sort_values("Planned", ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Planned Budget", y=dept_budget["department"], x=dept_budget["Planned"],
                         orientation="h", marker_color="#2563EB", opacity=0.85))
    fig.add_trace(go.Bar(name="Actual Spend YTD", y=dept_budget["department"], x=dept_budget["Actual_YTD"],
                         orientation="h", marker_color="#10B981", opacity=0.85))
    fig.add_trace(go.Bar(name="Forecast at Completion", y=dept_budget["department"], x=dept_budget["Forecast"],
                         orientation="h", marker_color="#F59E0B", opacity=0.85))
    fig.update_layout(barmode="group", xaxis_tickformat="$.0s",
                      legend=dict(orientation="h", y=1.08, x=0))
    apply_chart_theme(fig, height=340)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.markdown('<div class="section-header">Projects by Phase & Status</div>', unsafe_allow_html=True)
    phase_status = df.groupby(["phase", "status"])["project_id"].count().reset_index()
    phase_status.columns = ["phase", "status", "count"]
    phase_order = ["Initiation", "Planning", "Execution", "Monitoring & Control", "Closure"]
    phase_status["phase"] = pd.Categorical(phase_status["phase"], categories=phase_order, ordered=True)
    phase_status = phase_status.sort_values("phase")

    fig2 = px.bar(phase_status, x="phase", y="count", color="status",
                  color_discrete_map=STATUS_COLORS, barmode="stack",
                  labels={"count": "Projects", "phase": "", "status": "Status"})
    apply_chart_theme(fig2, height=340)
    st.plotly_chart(fig2, use_container_width=True)

# ── Gantt / Timeline View ───────────────────────────────────────────────────────
st.markdown('<div class="section-header">Project Timeline (Top 40 by Budget)</div>', unsafe_allow_html=True)

gantt_df = df.sort_values("estimated_budget", ascending=False).head(40).copy()
gantt_df = gantt_df.sort_values("planned_start_date")

fig_gantt = px.timeline(
    gantt_df,
    x_start="planned_start_date",
    x_end="forecast_end_date",
    y="project_name",
    color="status",
    color_discrete_map=STATUS_COLORS,
    hover_name="project_name",
    hover_data={"department": True, "project_manager": True, "completion_pct": True,
                "risk_score": ":.0f", "estimated_budget": ":$,.0f"},
    labels={"project_name": ""},
)
fig_gantt.add_vline(x="2025-04-25", line_dash="solid", line_color="#1E293B", line_width=2)
fig_gantt.add_annotation(
    x="2025-04-25", y=1, yref="paper", text="Today",
    showarrow=False, xanchor="left", yanchor="bottom",
    font=dict(color="#1E293B", size=11),
)
fig_gantt.update_yaxes(autorange="reversed", tickfont_size=10)
apply_chart_theme(fig_gantt, height=max(400, len(gantt_df) * 22))
fig_gantt.update_layout(margin=dict(l=220, r=20, t=40, b=20))
st.plotly_chart(fig_gantt, use_container_width=True)

# ── Strategic Portfolio View ────────────────────────────────────────────────────
c3, c4 = st.columns(2)

with c3:
    st.markdown('<div class="section-header">Strategic Priority vs Business Value</div>', unsafe_allow_html=True)
    priority_labels = {1: "1-Low", 2: "2-Below Avg", 3: "3-Medium", 4: "4-High", 5: "5-Critical"}
    df_prio = df.copy()
    df_prio["priority_label"] = df_prio["strategic_priority"].map(priority_labels)

    prio_agg = df_prio.groupby("priority_label").agg(
        avg_bv=("business_value_score", "mean"),
        avg_risk=("risk_score", "mean"),
        total_budget=("estimated_budget", "sum"),
        count=("project_id", "count"),
    ).reset_index().sort_values("priority_label")

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        name="Avg Business Value",
        x=prio_agg["priority_label"],
        y=prio_agg["avg_bv"],
        marker_color="#2563EB",
        yaxis="y",
        offsetgroup=1,
    ))
    fig3.add_trace(go.Bar(
        name="Avg Risk Score",
        x=prio_agg["priority_label"],
        y=prio_agg["avg_risk"],
        marker_color="#EF4444",
        yaxis="y",
        offsetgroup=2,
    ))
    fig3.update_layout(barmode="group", xaxis_title="", yaxis_title="Score (0–100)")
    apply_chart_theme(fig3, height=320)
    st.plotly_chart(fig3, use_container_width=True)

with c4:
    st.markdown('<div class="section-header">Budget Variance Distribution</div>', unsafe_allow_html=True)
    fig4 = px.histogram(
        df, x="budget_variance_pct", nbins=30, color="department",
        color_discrete_map=DEPT_COLORS,
        labels={"budget_variance_pct": "Budget Variance (%)", "count": "Projects"},
        opacity=0.8,
    )
    fig4.add_vline(x=0, line_dash="solid", line_color="#1E293B", line_width=2)
    fig4.add_vline(x=10, line_dash="dot", line_color="#F59E0B",
                   annotation_text="+10% warn", annotation_position="top right")
    fig4.add_vline(x=20, line_dash="dot", line_color="#EF4444",
                   annotation_text="+20% critical", annotation_position="top right")
    apply_chart_theme(fig4, height=320)
    st.plotly_chart(fig4, use_container_width=True)

# ── Project Table ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Full Project Inventory</div>', unsafe_allow_html=True)

table_cols = [
    "project_id", "project_name", "department", "program", "project_manager",
    "strategic_priority", "status", "phase", "completion_pct",
    "estimated_budget", "budget_variance_pct", "schedule_variance_days",
    "risk_level", "risk_score", "team_size", "issue_count",
]
display = df[table_cols].copy()
display = display.rename(columns={
    "project_id": "ID", "project_name": "Project Name", "department": "Dept",
    "program": "Program", "project_manager": "PM",
    "strategic_priority": "Priority", "status": "Status", "phase": "Phase",
    "completion_pct": "Done%", "estimated_budget": "Budget",
    "budget_variance_pct": "BV%", "schedule_variance_days": "Slip (d)",
    "risk_level": "Risk Level", "risk_score": "Risk", "team_size": "Team",
    "issue_count": "Issues",
})

st.dataframe(display, use_container_width=True, height=500)
st.caption(f"Showing {len(df)} of {len(projects)} projects after filters")
