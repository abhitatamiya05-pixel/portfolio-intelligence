import pandas as pd
import numpy as np


def compute_utilization(
    allocations: pd.DataFrame, resources: pd.DataFrame
) -> pd.DataFrame:
    merged = allocations.merge(
        resources[["resource_id", "resource_name", "role", "department", "monthly_capacity_hours", "cost_per_hour"]],
        on="resource_id",
    )
    util = (
        merged.groupby(["resource_id", "resource_name", "role", "department", "monthly_capacity_hours", "cost_per_hour", "month"])
        .agg(total_allocated=("allocated_hours", "sum"), n_projects=("project_id", "nunique"))
        .reset_index()
    )
    util["utilization_pct"] = (util["total_allocated"] / util["monthly_capacity_hours"] * 100).round(1)
    util["status"] = pd.cut(
        util["utilization_pct"],
        bins=[0, 70, 90, 110, float("inf")],
        labels=["Underutilized", "Optimal", "Near Capacity", "Overloaded"],
        right=True,
    )
    util["monthly_cost"] = (util["total_allocated"] * util["cost_per_hour"]).round(0)
    return util


def get_overloaded_resources(util: pd.DataFrame, threshold: float = 100.0, min_months: int = 2) -> pd.DataFrame:
    """Resources with sustained overload — must exceed threshold in at least min_months."""
    overloaded = util[util["utilization_pct"] > threshold].copy()
    summary = (
        overloaded.groupby(["resource_id", "resource_name", "role", "department"])
        .agg(
            peak_utilization=("utilization_pct", "max"),
            avg_utilization=("utilization_pct", "mean"),
            overloaded_months=("month", "count"),
            total_projects=("n_projects", "max"),
        )
        .reset_index()
        .query(f"overloaded_months >= {min_months}")
        .sort_values("peak_utilization", ascending=False)
        .round(1)
    )
    return summary


def get_demand_vs_capacity_by_role(
    allocations: pd.DataFrame, resources: pd.DataFrame
) -> pd.DataFrame:
    demand = (
        allocations.merge(resources[["resource_id", "role"]], on="resource_id")
        .groupby(["role", "month"])["allocated_hours"]
        .sum()
        .reset_index()
        .rename(columns={"allocated_hours": "total_demand_hours"})
    )
    capacity = (
        resources.assign(key=1)
        .merge(
            allocations[["month"]].drop_duplicates().assign(key=1),
            on="key",
        )
        .groupby(["role", "month"])["monthly_capacity_hours"]
        .sum()
        .reset_index()
        .rename(columns={"monthly_capacity_hours": "total_capacity_hours"})
    )
    merged = demand.merge(capacity, on=["role", "month"], how="outer").fillna(0)
    merged["gap_hours"] = merged["total_capacity_hours"] - merged["total_demand_hours"]
    merged["utilization_pct"] = (merged["total_demand_hours"] / merged["total_capacity_hours"].replace(0, 1) * 100).round(1)
    return merged


def get_resource_project_matrix(
    allocations: pd.DataFrame, resources: pd.DataFrame, latest_month: str | None = None
) -> pd.DataFrame:
    if latest_month:
        alloc = allocations[allocations["month"] == latest_month]
    else:
        latest = allocations["month"].max()
        alloc = allocations[allocations["month"] == latest]

    agg = alloc.groupby(["resource_id", "project_id"])["allocated_hours"].sum().reset_index()
    pivot = agg.pivot(index="resource_id", columns="project_id", values="allocated_hours").fillna(0)
    res_names = resources.set_index("resource_id")["resource_name"]
    pivot.index = pivot.index.map(res_names)
    return pivot


def top_bottleneck_resources(
    util: pd.DataFrame,
    projects: pd.DataFrame,
    allocations: pd.DataFrame,
    top_n: int = 10,
) -> pd.DataFrame:
    latest = allocations["month"].max()
    latest_alloc = allocations[allocations["month"] == latest]

    high_risk_pids = projects[projects["risk_level"].isin(["High", "Critical"])]["project_id"].tolist()
    high_risk_alloc = latest_alloc[latest_alloc["project_id"].isin(high_risk_pids)]

    critical_resources = (
        high_risk_alloc.groupby("resource_id")
        .agg(
            high_risk_project_count=("project_id", "nunique"),
            total_allocated_hours=("allocated_hours", "sum"),
        )
        .reset_index()
    )

    latest_util = util[util["month"] == latest][["resource_id", "resource_name", "role", "utilization_pct", "n_projects"]]
    bottlenecks = latest_util.merge(critical_resources, on="resource_id", how="left").fillna(0)
    bottlenecks["bottleneck_score"] = (
        bottlenecks["utilization_pct"] * 0.5
        + bottlenecks["high_risk_project_count"] * 8
        + bottlenecks["n_projects"] * 2
    )
    return bottlenecks.sort_values("bottleneck_score", ascending=False).head(top_n)


def portfolio_capacity_summary(util: pd.DataFrame) -> pd.DataFrame:
    return (
        util.groupby("month")
        .agg(
            avg_utilization=("utilization_pct", "mean"),
            overloaded_count=("utilization_pct", lambda x: (x > 100).sum()),
            underutilized_count=("utilization_pct", lambda x: (x < 70).sum()),
            total_cost=("monthly_cost", "sum"),
        )
        .reset_index()
        .round(1)
    )
