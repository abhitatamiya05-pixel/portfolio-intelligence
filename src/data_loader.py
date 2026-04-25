import streamlit as st
import pandas as pd
import numpy as np
from src.data_generator import generate_all_data

STATUS_COLORS = {
    "On Track": "#10B981",
    "At Risk": "#F59E0B",
    "Off Track": "#EF4444",
    "Completed": "#6366F1",
    "On Hold": "#94A3B8",
}

RISK_COLORS = {
    "Low": "#10B981",
    "Medium": "#F59E0B",
    "High": "#F97316",
    "Critical": "#EF4444",
}

DEPT_COLORS = {
    "IT": "#2563EB",
    "Operations": "#7C3AED",
    "Finance": "#059669",
    "Marketing": "#DB2777",
    "Product": "#D97706",
    "HR": "#0891B2",
}

CHART_LAYOUT = dict(
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    font=dict(family="Inter, sans-serif", size=13, color="#1E293B"),
    margin=dict(l=20, r=20, t=48, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)

GRID_STYLE = dict(showgrid=True, gridcolor="#F1F5F9", linecolor="#E2E8F0", zeroline=False)


@st.cache_data(show_spinner=False)
def load_data() -> dict[str, pd.DataFrame]:
    data = generate_all_data()

    projects = data["projects"]
    projects["planned_start_date"] = pd.to_datetime(projects["planned_start_date"])
    projects["planned_end_date"] = pd.to_datetime(projects["planned_end_date"])
    projects["actual_start_date"] = pd.to_datetime(projects["actual_start_date"])
    projects["forecast_end_date"] = pd.to_datetime(projects["forecast_end_date"])
    projects["last_updated"] = pd.to_datetime(projects["last_updated"])

    allocations = data["allocations"]
    allocations["month_dt"] = pd.to_datetime(allocations["month"] + "-01")

    return {**data, "projects": projects, "allocations": allocations}


def apply_chart_theme(fig, height: int = 420):
    fig.update_layout(**CHART_LAYOUT, height=height)
    fig.update_xaxes(**GRID_STYLE)
    fig.update_yaxes(**GRID_STYLE)
    return fig


def fmt_currency(value: float, decimals: int = 1) -> str:
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.{decimals}f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.{decimals}f}M"
    if value >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:,.0f}"


def portfolio_kpis(projects: pd.DataFrame) -> dict:
    active = projects[projects["status"] != "Completed"]
    total_budget = projects["estimated_budget"].sum()
    total_forecast = projects["forecast_at_completion"].sum()
    at_risk = projects[projects["status"].isin(["At Risk", "Off Track"])]
    critical = projects[projects["risk_level"] == "Critical"]

    return {
        "total_portfolio_value": total_budget,
        "total_forecast": total_forecast,
        "budget_variance_pct": round((total_forecast - total_budget) / total_budget * 100, 1),
        "project_count": len(projects),
        "active_count": len(active),
        "at_risk_count": len(at_risk),
        "at_risk_pct": round(len(at_risk) / len(projects) * 100, 1),
        "critical_count": len(critical),
        "completed_count": len(projects[projects["status"] == "Completed"]),
        "avg_health": round(projects["health_index"].mean(), 1),
        "avg_completion": round(active["completion_pct"].mean(), 1),
        "avg_risk_score": round(projects["risk_score"].mean(), 1),
    }


def filter_projects(
    projects: pd.DataFrame,
    departments: list[str] | None = None,
    statuses: list[str] | None = None,
    priorities: list[int] | None = None,
    phases: list[str] | None = None,
    risk_levels: list[str] | None = None,
) -> pd.DataFrame:
    df = projects.copy()
    if departments:
        df = df[df["department"].isin(departments)]
    if statuses:
        df = df[df["status"].isin(statuses)]
    if priorities:
        df = df[df["strategic_priority"].isin(priorities)]
    if phases:
        df = df[df["phase"].isin(phases)]
    if risk_levels:
        df = df[df["risk_level"].isin(risk_levels)]
    return df
