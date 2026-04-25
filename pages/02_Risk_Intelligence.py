import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from src.data_loader import load_data, apply_chart_theme, fmt_currency, STATUS_COLORS, RISK_COLORS, DEPT_COLORS
from src.risk_model import (
    train_risk_model, predict_risk, get_feature_importances,
    flag_risk_divergence, compute_risk_trend, department_risk_summary,
)

st.set_page_config(page_title="Risk Intelligence", page_icon="🎯", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .section-header { font-size: 1.05rem; font-weight: 600; color: #1E293B;
                      border-bottom: 2px solid #E2E8F0; padding-bottom: 0.4rem;
                      margin: 1.2rem 0 0.8rem; }
    .risk-badge-critical { background:#FEE2E2;color:#B91C1C;padding:2px 8px;
                           border-radius:12px;font-weight:700;font-size:0.8rem; }
    .risk-badge-high { background:#FFEDD5;color:#C2410C;padding:2px 8px;
                       border-radius:12px;font-weight:700;font-size:0.8rem; }
</style>
""", unsafe_allow_html=True)

data = load_data()
projects = data["projects"]
monthly_metrics = data["monthly_metrics"]

st.markdown("## Risk Intelligence")
st.caption("ML-powered risk scoring, risk matrix analysis, and portfolio risk trends")

# ── Train model ────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_model(n_projects: int):
    return train_risk_model(projects)

with st.spinner("Training risk model..."):
    model, le = get_model(len(projects))

projects_pred = predict_risk(model, le, projects)
feature_imp = get_feature_importances(model)

# ── Sidebar filters ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Filters")
    sel_depts = st.multiselect("Department", sorted(projects["department"].unique()), default=[])
    sel_risk = st.multiselect("Risk Level", ["Critical", "High", "Medium", "Low"], default=[])
    sel_status = st.multiselect("Status", sorted(projects["status"].unique()), default=[])
    min_risk = st.slider("Min Risk Score", 0, 100, 0)

df = projects_pred.copy()
if sel_depts: df = df[df["department"].isin(sel_depts)]
if sel_risk:  df = df[df["risk_level"].isin(sel_risk)]
if sel_status: df = df[df["status"].isin(sel_status)]
df = df[df["risk_score"] >= min_risk]

# ── Risk summary metrics ────────────────────────────────────────────────────────
m1, m2, m3, m4, m5 = st.columns(5)
cols_metrics = [
    (str(df[df["risk_level"] == "Critical"].shape[0]), "Critical Risk", "#EF4444"),
    (str(df[df["risk_level"] == "High"].shape[0]), "High Risk", "#F97316"),
    (str(df[df["risk_level"] == "Medium"].shape[0]), "Medium Risk", "#F59E0B"),
    (fmt_currency(df[df["risk_level"].isin(["Critical","High"])]["estimated_budget"].sum()), "Budget at Risk", "#EF4444"),
    (f"{df['risk_score'].mean():.0f}", "Avg Risk Score", "#1E293B"),
]
for col, (val, lbl, color) in zip([m1, m2, m3, m4, m5], cols_metrics):
    col.metric(lbl, val)

st.markdown("---")

# ── Row 1: Risk Matrix + Feature Importances ───────────────────────────────────
c1, c2 = st.columns([1.6, 1.4])

with c1:
    st.markdown('<div class="section-header">Risk Matrix — Probability vs Impact</div>', unsafe_allow_html=True)
    active = df[df["status"] != "Completed"].copy()

    fig = px.scatter(
        active,
        x="risk_probability",
        y="risk_impact",
        size="estimated_budget",
        color="risk_level",
        color_discrete_map=RISK_COLORS,
        hover_name="project_name",
        hover_data={
            "department": True, "status": True, "risk_score": ":.0f",
            "estimated_budget": ":$,.0f", "project_manager": True,
            "risk_probability": ":.2f", "risk_impact": ":.2f",
        },
        size_max=30,
        labels={"risk_probability": "Risk Probability", "risk_impact": "Business Impact"},
        category_orders={"risk_level": ["Low", "Medium", "High", "Critical"]},
    )
    # Quadrant shading
    fig.add_shape(type="rect", x0=0.5, y0=0.5, x1=1.0, y1=1.0,
                  fillcolor="rgba(239,68,68,0.08)", line_width=0)
    fig.add_shape(type="rect", x0=0, y0=0, x1=0.5, y1=0.5,
                  fillcolor="rgba(16,185,129,0.05)", line_width=0)
    fig.add_vline(x=0.5, line_dash="dot", line_color="#94A3B8")
    fig.add_hline(y=0.5, line_dash="dot", line_color="#94A3B8")

    fig.add_annotation(x=0.75, y=0.92, text="⚠️ Action Zone", showarrow=False,
                       font=dict(color="#B91C1C", size=11, family="Inter"))
    fig.add_annotation(x=0.15, y=0.08, text="✓ Monitor", showarrow=False,
                       font=dict(color="#059669", size=11, family="Inter"))
    apply_chart_theme(fig, height=400)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.markdown('<div class="section-header">ML Risk Model — Feature Importances</div>', unsafe_allow_html=True)
    fig2 = px.bar(
        feature_imp, x="importance", y="label", orientation="h",
        color="importance",
        color_continuous_scale=["#DBEAFE", "#2563EB"],
        labels={"importance": "Importance", "label": ""},
        text=feature_imp["importance"].map("{:.1%}".format),
    )
    fig2.update_traces(textposition="outside", showlegend=False)
    fig2.update_coloraxes(showscale=False)
    apply_chart_theme(fig2, height=400)
    fig2.update_layout(margin=dict(l=10, r=60, t=40, b=20))
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("GradientBoosting model trained on portfolio risk features. "
               "Higher importance = stronger predictor of risk outcome.")

# ── Row 2: Risk Trend + Department Radar ───────────────────────────────────────
c3, c4 = st.columns(2)

with c3:
    st.markdown('<div class="section-header">Portfolio Risk Trend (Last 6 Months)</div>', unsafe_allow_html=True)
    risk_trend = compute_risk_trend(monthly_metrics)
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=risk_trend["month"], y=risk_trend["max_risk"],
        mode="lines", name="Max Risk", line=dict(color="#EF4444", dash="dot", width=1.5),
        fill=None,
    ))
    fig3.add_trace(go.Scatter(
        x=risk_trend["month"], y=risk_trend["avg_risk"],
        mode="lines+markers", name="Avg Risk", line=dict(color="#2563EB", width=2.5),
        marker=dict(size=7),
        fill="tonexty", fillcolor="rgba(239,68,68,0.06)",
    ))
    fig3.add_trace(go.Scatter(
        x=risk_trend["month"], y=risk_trend["median_risk"],
        mode="lines", name="Median Risk", line=dict(color="#6366F1", dash="dash", width=1.5),
    ))
    fig3.add_hline(y=50, line_dash="dot", line_color="#F59E0B",
                   annotation_text="High risk threshold")
    fig3.update_layout(yaxis_title="Risk Score", xaxis_title="")
    apply_chart_theme(fig3, height=340)
    st.plotly_chart(fig3, use_container_width=True)

with c4:
    st.markdown('<div class="section-header">Department Risk Radar</div>', unsafe_allow_html=True)
    dept_risk = department_risk_summary(projects)

    fig4 = go.Figure()
    categories = dept_risk["department"].tolist()
    categories_closed = categories + [categories[0]]
    values = dept_risk["avg_risk"].tolist()
    values_closed = values + [values[0]]

    fig4.add_trace(go.Scatterpolar(
        r=values_closed, theta=categories_closed,
        fill="toself", name="Avg Risk Score",
        line_color="#2563EB", fillcolor="rgba(37,99,235,0.12)",
    ))
    fig4.add_trace(go.Scatterpolar(
        r=dept_risk["at_risk_pct"].tolist() + [dept_risk["at_risk_pct"].tolist()[0]],
        theta=categories_closed,
        fill="toself", name="At-Risk Project %",
        line_color="#EF4444", fillcolor="rgba(239,68,68,0.08)",
    ))
    fig4.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 80])),
        legend=dict(orientation="h", y=-0.12),
        plot_bgcolor="#FFF", paper_bgcolor="#FFF",
        margin=dict(l=40, r=40, t=40, b=60), height=340,
        font=dict(family="Inter, sans-serif", size=12, color="#1E293B"),
    )
    st.plotly_chart(fig4, use_container_width=True)

# ── Row 3: Risk Divergence + Critical Projects Table ──────────────────────────
c5, c6 = st.columns([1, 1.2])

with c5:
    st.markdown('<div class="section-header">Model vs Self-Reported Risk Divergence</div>', unsafe_allow_html=True)
    diverged = flag_risk_divergence(projects_pred)
    upward = diverged[diverged["risk_divergence"] > 0]
    downward = diverged[diverged["risk_divergence"] < 0]

    st.markdown(f"**{len(upward)}** projects where model predicts **higher** risk than reported  "
                f"· **{len(downward)}** where model predicts **lower** risk")

    if len(upward) > 0:
        st.markdown("**⬆ Under-reported risk (model says higher)**")
        show_up = upward.head(8)[["project_name", "department", "risk_level", "predicted_risk_level", "risk_score"]]\
            .rename(columns={"project_name": "Project", "department": "Dept",
                             "risk_level": "Reported", "predicted_risk_level": "ML Predicts", "risk_score": "Score"})
        st.dataframe(show_up, use_container_width=True, height=220)

    if len(downward) > 0:
        st.markdown("**⬇ Over-reported risk (model says lower)**")
        show_dn = downward.tail(5)[["project_name", "risk_level", "predicted_risk_level"]]\
            .rename(columns={"project_name": "Project", "risk_level": "Reported", "predicted_risk_level": "ML Predicts"})
        st.dataframe(show_dn, use_container_width=True, height=160)

with c6:
    st.markdown('<div class="section-header">Critical & High Risk Projects — Action Required</div>', unsafe_allow_html=True)

    urgent = df[df["risk_level"].isin(["Critical", "High"]) & df["status"].isin(["At Risk", "Off Track"])]\
        .sort_values(["risk_score", "business_value_score"], ascending=[False, False])\
        .head(15)[["project_name", "department", "project_manager", "risk_level", "risk_score",
                   "budget_variance_pct", "schedule_variance_days", "issue_count", "completion_pct"]]

    urgent = urgent.rename(columns={
        "project_name": "Project", "department": "Dept", "project_manager": "PM",
        "risk_level": "Risk", "risk_score": "Score", "budget_variance_pct": "BV%",
        "schedule_variance_days": "Slip (d)", "issue_count": "Issues", "completion_pct": "Done%",
    })

    st.dataframe(urgent, use_container_width=True, height=420)

# ── Risk by Department Heat Table ──────────────────────────────────────────────
st.markdown('<div class="section-header">Risk Breakdown by Department</div>', unsafe_allow_html=True)

dept_summary = department_risk_summary(projects)
dept_summary["total_budget_at_risk_fmt"] = dept_summary["total_budget_at_risk"].apply(fmt_currency)
dept_summary = dept_summary.rename(columns={
    "department": "Department", "avg_risk": "Avg Risk Score",
    "critical_count": "Critical", "high_count": "High",
    "at_risk_pct": "At-Risk %", "total_projects": "Projects",
    "total_budget_at_risk_fmt": "Budget at Risk",
})

st.dataframe(dept_summary, use_container_width=True, height=280)
