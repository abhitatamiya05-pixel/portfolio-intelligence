import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from src.data_loader import load_data, apply_chart_theme, fmt_currency, DEPT_COLORS
from src.resource_analyzer import (
    compute_utilization, get_overloaded_resources,
    get_demand_vs_capacity_by_role, top_bottleneck_resources,
    portfolio_capacity_summary,
)

st.set_page_config(page_title="Resource Intelligence", page_icon="👥", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .section-header { font-size: 1.05rem; font-weight: 600; color: #1E293B;
                      border-bottom: 2px solid #E2E8F0; padding-bottom: 0.4rem;
                      margin: 1.2rem 0 0.8rem; }
    .alert-overload { background:#FEE2E2; border-left:4px solid #EF4444;
                      padding:0.5rem 0.9rem; border-radius:0 6px 6px 0; margin-bottom:0.3rem;
                      font-size:0.88rem; }
    .util-badge { display:inline-block; padding:2px 8px; border-radius:12px;
                  font-size:0.78rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)

data = load_data()
projects = data["projects"]
resources = data["resources"]
allocations = data["allocations"]

st.markdown("## Resource Intelligence")
st.caption("Capacity utilization, bottleneck detection, and resource demand planning")

# ── Compute analytics ──────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def compute_all(alloc_hash: int):
    util = compute_utilization(allocations, resources)
    overloaded = get_overloaded_resources(util)
    demand_cap = get_demand_vs_capacity_by_role(allocations, resources)
    cap_summary = portfolio_capacity_summary(util)
    bottlenecks = top_bottleneck_resources(util, projects, allocations)
    return util, overloaded, demand_cap, cap_summary, bottlenecks

util, overloaded, demand_cap, cap_summary, bottlenecks = compute_all(len(allocations))

# ── Sidebar filters ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Filters")
    sel_roles = st.multiselect("Role", sorted(resources["role"].unique()), default=[])
    sel_depts = st.multiselect("Department", sorted(resources["department"].unique()), default=[])
    util_filter = st.selectbox("Utilization Status", ["All", "Overloaded (>100%)", "Near Capacity (90-100%)",
                                                        "Optimal (70-90%)", "Underutilized (<70%)"])
    selected_month = st.selectbox("Month", sorted(util["month"].unique(), reverse=True))

util_filtered = util.copy()
if sel_roles:
    util_filtered = util_filtered[util_filtered["role"].isin(sel_roles)]
if sel_depts:
    util_filtered = util_filtered[util_filtered["department"].isin(sel_depts)]
util_filter_map = {
    "Overloaded (>100%)": "Overloaded", "Near Capacity (90-100%)": "Near Capacity",
    "Optimal (70-90%)": "Optimal", "Underutilized (<70%)": "Underutilized",
}
if util_filter in util_filter_map:
    util_filtered = util_filtered[util_filtered["status"] == util_filter_map[util_filter]]

# ── KPI Row ────────────────────────────────────────────────────────────────────
latest_util = util[util["month"] == util["month"].max()]
m1, m2, m3, m4, m5 = st.columns(5)

metrics = [
    (str(len(resources)), "Total Resources"),
    (f"{latest_util['utilization_pct'].mean():.0f}%", "Avg Utilization (Latest)"),
    (str(len(overloaded)), "Overloaded Resources"),
    (str(len(latest_util[latest_util["utilization_pct"] < 70])), "Underutilized Resources"),
    (fmt_currency(latest_util["monthly_cost"].sum()), "Est. Monthly Resource Cost"),
]
for col, (val, lbl) in zip([m1, m2, m3, m4, m5], metrics):
    col.metric(lbl, val)

st.markdown("---")

# ── Row 1: Utilization Heatmap + Overloaded Alerts ────────────────────────────
c1, c2 = st.columns([1.8, 1.2])

with c1:
    st.markdown('<div class="section-header">Resource Utilization Heatmap (Top 35 Resources)</div>',
                unsafe_allow_html=True)
    top_resources = (
        util.groupby("resource_id")["utilization_pct"].mean()
        .sort_values(ascending=False).head(35).index.tolist()
    )
    heat_data = util[util["resource_id"].isin(top_resources)].copy()
    heat_pivot = heat_data.pivot_table(
        index="resource_name", columns="month", values="utilization_pct", aggfunc="mean"
    ).fillna(0)

    colorscale = [
        [0.0,  "#DBEAFE"], [0.4,  "#93C5FD"], [0.6,  "#3B82F6"],
        [0.8,  "#1D4ED8"], [0.9,  "#F59E0B"], [1.0,  "#EF4444"],
    ]
    fig = go.Figure(go.Heatmap(
        z=heat_pivot.values,
        x=heat_pivot.columns.tolist(),
        y=heat_pivot.index.tolist(),
        colorscale=colorscale,
        zmin=0, zmax=140,
        colorbar=dict(title="Util %", tickvals=[0, 50, 70, 90, 100, 120, 140],
                      ticktext=["0%", "50%", "70%", "90%", "100%", "120%", "140%"]),
        hovertemplate="<b>%{y}</b><br>Month: %{x}<br>Utilization: %{z:.0f}%<extra></extra>",
    ))
    # Overload threshold line annotation
    fig.add_shape(type="line", x0=-0.5, x1=len(heat_pivot.columns) - 0.5,
                  y0=-0.5, y1=-0.5, line=dict(color="rgba(0,0,0,0)", width=0))
    apply_chart_theme(fig, height=max(380, len(heat_pivot) * 18))
    fig.update_layout(margin=dict(l=160, r=20, t=40, b=40),
                      xaxis=dict(side="top"))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.markdown('<div class="section-header">Overloaded Resource Alerts</div>', unsafe_allow_html=True)
    if len(overloaded) > 0:
        st.markdown(f"**{len(overloaded)}** resources have sustained overload across reporting period")
        for _, row in overloaded.head(12).iterrows():
            color = "#EF4444" if row["peak_utilization"] > 120 else "#F59E0B"
            st.markdown(f"""
            <div style="background:{color}15;border-left:3px solid {color};
                        padding:0.5rem 0.8rem;border-radius:0 6px 6px 0;margin-bottom:0.4rem;">
            <b>{row['resource_name']}</b> · {row['role']}<br>
            <span style="color:{color};font-weight:700">{row['peak_utilization']:.0f}% peak</span>
            &nbsp;·&nbsp; {row['overloaded_months']:.0f} months overloaded
            &nbsp;·&nbsp; {row['total_projects']:.0f} projects
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("No resources are currently overloaded")

# ── Row 2: Demand vs Capacity by Role ──────────────────────────────────────────
st.markdown('<div class="section-header">Role-Level Demand vs Capacity</div>', unsafe_allow_html=True)

latest_demand = demand_cap[demand_cap["month"] == demand_cap["month"].max()].copy()
latest_demand = latest_demand.sort_values("utilization_pct", ascending=False)

fig2 = go.Figure()
fig2.add_trace(go.Bar(
    name="Total Capacity", x=latest_demand["role"], y=latest_demand["total_capacity_hours"],
    marker_color="#DBEAFE", marker_line=dict(color="#2563EB", width=1),
))
fig2.add_trace(go.Bar(
    name="Total Demand", x=latest_demand["role"], y=latest_demand["total_demand_hours"],
    marker_color="#2563EB", opacity=0.85,
))
fig2.add_trace(go.Scatter(
    name="Utilization %", x=latest_demand["role"], y=latest_demand["utilization_pct"],
    mode="lines+markers", yaxis="y2", line=dict(color="#EF4444", width=2),
    marker=dict(size=8, color="#EF4444"),
))
fig2.update_layout(
    barmode="overlay",
    yaxis=dict(title="Hours"),
    yaxis2=dict(title="Utilization %", overlaying="y", side="right", range=[0, 160],
                tickformat=".0f%%"),
    xaxis=dict(tickangle=-30),
)
apply_chart_theme(fig2, height=380)
st.plotly_chart(fig2, use_container_width=True)

# ── Row 3: Capacity Trend + Bottleneck Table ────────────────────────────────────
c3, c4 = st.columns([1.2, 1.8])

with c3:
    st.markdown('<div class="section-header">Portfolio Capacity Trend</div>', unsafe_allow_html=True)
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=cap_summary["month"], y=cap_summary["avg_utilization"],
        mode="lines+markers", name="Avg Utilization %",
        line=dict(color="#2563EB", width=2.5), marker=dict(size=8),
        fill="tozeroy", fillcolor="rgba(37,99,235,0.08)",
    ))
    fig3.add_trace(go.Bar(
        x=cap_summary["month"], y=cap_summary["overloaded_count"],
        name="Overloaded Resources", marker_color="rgba(239,68,68,0.31)", yaxis="y2",
    ))
    fig3.add_hline(y=100, line_dash="dot", line_color="#EF4444",
                   annotation_text="100% threshold")
    fig3.add_hline(y=85, line_dash="dot", line_color="#F59E0B",
                   annotation_text="85% target")
    fig3.update_layout(
        yaxis=dict(title="Avg Utilization %", range=[0, 130]),
        yaxis2=dict(title="# Overloaded", overlaying="y", side="right"),
    )
    apply_chart_theme(fig3, height=340)
    st.plotly_chart(fig3, use_container_width=True)

with c4:
    st.markdown('<div class="section-header">Critical Resource Bottlenecks</div>', unsafe_allow_html=True)
    st.caption("Resources that are both overloaded AND assigned to high/critical risk projects")

    bt_display = bottlenecks[[
        "resource_name", "role", "utilization_pct", "n_projects",
        "high_risk_project_count", "bottleneck_score"
    ]].rename(columns={
        "resource_name": "Resource", "role": "Role",
        "utilization_pct": "Util %", "n_projects": "Active Projects",
        "high_risk_project_count": "High-Risk Projects", "bottleneck_score": "Bottleneck Score",
    })

    st.dataframe(bt_display, use_container_width=True, height=340)

# ── Resource table ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Full Resource Roster with Latest Utilization</div>',
            unsafe_allow_html=True)

latest_per_resource = (
    util[util["month"] == util["month"].max()]
    .groupby(["resource_id", "resource_name", "role", "department"])[["utilization_pct", "n_projects", "monthly_cost"]]
    .first()
    .reset_index()
)
full_roster = resources.merge(
    latest_per_resource[["resource_id", "utilization_pct", "n_projects", "monthly_cost"]],
    on="resource_id", how="left",
).fillna({"utilization_pct": 0, "n_projects": 0, "monthly_cost": 0})

if sel_roles:
    full_roster = full_roster[full_roster["role"].isin(sel_roles)]
if sel_depts:
    full_roster = full_roster[full_roster["department"].isin(sel_depts)]

display_roster = full_roster[[
    "resource_name", "role", "department", "seniority",
    "monthly_capacity_hours", "cost_per_hour", "utilization_pct", "n_projects", "monthly_cost"
]].rename(columns={
    "resource_name": "Name", "role": "Role", "department": "Dept", "seniority": "Level",
    "monthly_capacity_hours": "Capacity (hrs)", "cost_per_hour": "$/hr",
    "utilization_pct": "Util %", "n_projects": "Projects", "monthly_cost": "Est. Monthly Cost",
}).sort_values("Util %", ascending=False)

st.dataframe(display_roster, use_container_width=True, height=420)
st.caption(f"Showing {len(display_roster)} of {len(resources)} resources")
