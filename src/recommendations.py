import pandas as pd
import numpy as np
from datetime import date

TODAY = date(2025, 4, 25)


def generate_recommendations(
    projects: pd.DataFrame,
    resources: pd.DataFrame,
    util: pd.DataFrame,
    overloaded: pd.DataFrame,
) -> list[dict]:
    recs = []

    # 1. Critical projects with low completion
    critical_low = projects[
        (projects["risk_level"] == "Critical") & (projects["completion_pct"] < 50)
        & (projects["status"] != "Completed")
    ].sort_values("business_value_score", ascending=False)
    if len(critical_low) > 0:
        names = ", ".join(critical_low.head(3)["project_name"].tolist())
        recs.append({
            "category": "Risk",
            "priority": "Critical",
            "title": f"{len(critical_low)} critical-risk projects are less than 50% complete",
            "detail": f"Immediate intervention required for: {names}. These projects combine high risk scores with low delivery progress.",
            "action": "Schedule emergency steering committee review. Assign senior PMO oversight and consider scope reduction.",
            "metric": f"{len(critical_low)} projects · Avg risk: {critical_low['risk_score'].mean():.0f}/100",
            "icon": "🔴",
        })

    # 2. Budget overrun with high value
    budget_alert = projects[
        (projects["budget_variance_pct"] > 20)
        & (projects["business_value_score"] >= 60)
        & (projects["status"] != "Completed")
    ].sort_values("budget_variance_pct", ascending=False)
    if len(budget_alert) > 0:
        total_overrun = (budget_alert["forecast_at_completion"] - budget_alert["estimated_budget"]).sum()
        recs.append({
            "category": "Budget",
            "priority": "High",
            "title": f"{len(budget_alert)} high-value projects are tracking >20% over budget",
            "detail": f"Total projected overrun: ${total_overrun/1e6:.1f}M across {len(budget_alert)} strategic projects.",
            "action": "Conduct budget reforecast with project managers. Identify scope items that can be deferred to Phase 2.",
            "metric": f"${total_overrun/1e6:.1f}M total overrun",
            "icon": "💰",
        })

    # 3. Schedule slip on high priority
    schedule_slip = projects[
        (projects["schedule_variance_days"] > 30)
        & (projects["strategic_priority"] >= 4)
        & (projects["status"] != "Completed")
    ].sort_values("schedule_variance_days", ascending=False)
    if len(schedule_slip) > 0:
        avg_slip = schedule_slip["schedule_variance_days"].mean()
        recs.append({
            "category": "Schedule",
            "priority": "High",
            "title": f"{len(schedule_slip)} high-priority projects are slipping by 30+ days",
            "detail": f"Average slip of {avg_slip:.0f} days on Priority 4-5 projects threatens strategic delivery commitments.",
            "action": "Review critical path dependencies. Consider fast-tracking or crashing activities where ROI justifies cost.",
            "metric": f"Avg {avg_slip:.0f} day slip",
            "icon": "📅",
        })

    # 4. Overloaded project managers
    pm_load = (
        projects[projects["status"].isin(["On Track", "At Risk", "Off Track"])]
        .groupby("project_manager")
        .agg(project_count=("project_id", "count"), avg_risk=("risk_score", "mean"))
        .reset_index()
    )
    overloaded_pms = pm_load[pm_load["project_count"] >= 6].sort_values("project_count", ascending=False)
    if len(overloaded_pms) > 0:
        pm_names = ", ".join(overloaded_pms.head(3)["project_manager"].tolist())
        recs.append({
            "category": "Resources",
            "priority": "High",
            "title": f"{len(overloaded_pms)} project managers are carrying 6+ concurrent projects",
            "detail": f"Overloaded PMs: {pm_names}. Research shows PM effectiveness drops sharply above 5 concurrent projects.",
            "action": "Rebalance portfolio assignments. Promote senior BAs to act as deputy PMs on lower-complexity projects.",
            "metric": f"Max load: {overloaded_pms['project_count'].max()} projects/PM",
            "icon": "👤",
        })

    # 5. Resource overload
    if len(overloaded) > 0:
        avg_peak = overloaded["peak_utilization"].mean()
        recs.append({
            "category": "Resources",
            "priority": "Medium",
            "title": f"{len(overloaded)} resources are operating above 100% capacity",
            "detail": f"Average peak utilization at {avg_peak:.0f}%. Sustained overload leads to burnout and quality degradation.",
            "action": "Identify tasks that can be redistributed. Consider contractor augmentation for peak periods.",
            "metric": f"Avg peak: {avg_peak:.0f}%",
            "icon": "⚡",
        })

    # 6. Dependency bottlenecks
    dep_risk = projects[
        (projects["dependencies_count"] >= 5)
        & (projects["status"].isin(["At Risk", "Off Track"]))
    ]
    if len(dep_risk) > 0:
        recs.append({
            "category": "Dependencies",
            "priority": "Medium",
            "title": f"{len(dep_risk)} at-risk projects have 5+ upstream dependencies",
            "detail": "High dependency count combined with at-risk status creates cascading delay risk across the portfolio.",
            "action": "Map critical dependency chains. Escalate blockers to portfolio governance board for resolution.",
            "metric": f"{len(dep_risk)} projects at risk",
            "icon": "🔗",
        })

    # 7. Stalled projects
    stalled = projects[
        (projects["status"] == "On Hold")
        & (projects["business_value_score"] >= 50)
    ]
    if len(stalled) > 0:
        stalled_value = stalled["estimated_budget"].sum()
        recs.append({
            "category": "Portfolio",
            "priority": "Medium",
            "title": f"{len(stalled)} medium-high value projects are on hold",
            "detail": f"${stalled_value/1e6:.1f}M in approved budget is idle. Opportunity cost grows with each passing quarter.",
            "action": "Review hold reasons. Re-activate projects where blockers are resolved or cancel and reallocate budget.",
            "metric": f"${stalled_value/1e6:.1f}M idle budget",
            "icon": "⏸️",
        })

    # 8. Low-value, high-risk projects
    low_value_high_risk = projects[
        (projects["business_value_score"] <= 30)
        & (projects["risk_level"].isin(["High", "Critical"]))
        & (projects["status"] != "Completed")
    ]
    if len(low_value_high_risk) > 0:
        saved_budget = low_value_high_risk["estimated_budget"].sum()
        recs.append({
            "category": "Portfolio",
            "priority": "Medium",
            "title": f"{len(low_value_high_risk)} projects have low value but high risk — cancellation candidates",
            "detail": "These projects consume resources and risk capacity without proportional strategic return.",
            "action": f"Review with sponsors. Cancelling or deferring these could free up ~${saved_budget/1e6:.1f}M for higher-value work.",
            "metric": f"${saved_budget/1e6:.1f}M reclaimable",
            "icon": "✂️",
        })

    return sorted(recs, key=lambda r: {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}[r["priority"]])


def generate_executive_narrative(
    projects: pd.DataFrame,
    util: pd.DataFrame,
    kpis: dict,
) -> dict[str, str]:
    total_val = kpis["total_portfolio_value"]
    bv = kpis["budget_variance_pct"]
    health = kpis["avg_health"]
    at_risk_pct = kpis["at_risk_pct"]

    status_dist = projects["status"].value_counts(normalize=True).mul(100).round(1)
    risk_dist = projects["risk_level"].value_counts()
    dept_risk = projects.groupby("department")["risk_score"].mean().sort_values(ascending=False)
    top_risk_dept = dept_risk.index[0]

    latest_month = util["month"].max() if len(util) > 0 else "N/A"
    overloaded_pct = (util[util["month"] == latest_month]["utilization_pct"] > 100).mean() * 100 if len(util) > 0 else 0

    health_label = "strong" if health >= 70 else "moderate" if health >= 55 else "under stress"

    narrative = {
        "portfolio_health": (
            f"As of {TODAY.strftime('%B %d, %Y')}, the portfolio of **{kpis['project_count']} projects** "
            f"representing **${total_val/1e6:.0f}M** in approved investment is in **{health_label}** condition "
            f"with an average health index of **{health}/100**. "
            f"{status_dist.get('On Track', 0):.0f}% of projects are on track while "
            f"**{at_risk_pct}% ({kpis['at_risk_count']} projects)** are at risk or off track. "
            f"The portfolio currently forecasts a **{'+' if bv > 0 else ''}{bv}% budget variance**, "
            f"representing a total forecast overrun of "
            f"**${(kpis['total_forecast'] - total_val)/1e6:.1f}M**."
        ),
        "risk_summary": (
            f"The portfolio carries **{risk_dist.get('Critical', 0)} critical** and "
            f"**{risk_dist.get('High', 0)} high** risk projects requiring leadership attention. "
            f"**{top_risk_dept}** has the highest average risk score at "
            f"**{dept_risk.iloc[0]:.0f}/100**, driven by a combination of schedule slippage, "
            f"issue accumulation, and dependency complexity. "
            f"The average portfolio risk score is **{kpis['avg_risk_score']:.0f}/100**."
        ),
        "resource_summary": (
            f"Resource analysis covering the latest reporting period shows "
            f"**{overloaded_pct:.0f}%** of active resources operating above 100% capacity. "
            f"This creates execution risk on delivery timelines and is a leading indicator "
            f"of future schedule slippage. Immediate rebalancing is recommended for resources "
            f"sustaining overload across multiple consecutive months."
        ),
        "strategic_alignment": (
            f"Of the {kpis['project_count']} portfolio projects, "
            f"**{len(projects[projects['strategic_priority'] >= 4])}** are rated Priority 4 or 5 (strategic/critical). "
            f"These high-priority projects account for "
            f"**${projects[projects['strategic_priority'] >= 4]['estimated_budget'].sum()/1e6:.0f}M** "
            f"({projects[projects['strategic_priority'] >= 4]['estimated_budget'].sum() / total_val * 100:.0f}%) "
            f"of total portfolio investment. "
            f"Average business value score across the portfolio is "
            f"**{projects['business_value_score'].mean():.0f}/100**."
        ),
    }
    return narrative
