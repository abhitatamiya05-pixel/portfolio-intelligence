import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score
from sklearn.metrics import classification_report
import warnings

warnings.filterwarnings("ignore")

FEATURES = [
    "budget_variance_pct",
    "schedule_variance_days",
    "issue_count",
    "critical_issues",
    "change_requests",
    "complexity_score",
    "dependencies_count",
    "team_size",
    "completion_pct",
    "strategic_priority",
]

RISK_ORDER = ["Low", "Medium", "High", "Critical"]


def train_risk_model(projects: pd.DataFrame):
    df = projects.dropna(subset=FEATURES + ["risk_level"]).copy()

    X = df[FEATURES].values
    y = df["risk_level"].values

    le = LabelEncoder()
    le.fit(RISK_ORDER)
    y_enc = le.transform(y)

    model = GradientBoostingClassifier(
        n_estimators=120, max_depth=4, learning_rate=0.08,
        subsample=0.85, random_state=42,
    )
    model.fit(X, y_enc)

    return model, le


def predict_risk(model, le, projects: pd.DataFrame) -> pd.DataFrame:
    df = projects.copy()
    X = df[FEATURES].fillna(0).values
    probs = model.predict_proba(X)
    preds = model.predict(X)

    df["predicted_risk_level"] = le.inverse_transform(preds)
    df["risk_prob_low"] = probs[:, le.transform(["Low"])[0]]
    df["risk_prob_medium"] = probs[:, le.transform(["Medium"])[0]]
    df["risk_prob_high"] = probs[:, le.transform(["High"])[0]]
    df["risk_prob_critical"] = probs[:, le.transform(["Critical"])[0]]
    df["ml_risk_score"] = (
        df["risk_prob_low"] * 12.5
        + df["risk_prob_medium"] * 37.5
        + df["risk_prob_high"] * 62.5
        + df["risk_prob_critical"] * 87.5
    )

    return df


def get_feature_importances(model) -> pd.DataFrame:
    importances = model.feature_importances_
    labels = {
        "budget_variance_pct": "Budget Variance %",
        "schedule_variance_days": "Schedule Slip (days)",
        "issue_count": "Open Issues",
        "critical_issues": "Critical Issues",
        "change_requests": "Change Requests",
        "complexity_score": "Complexity",
        "dependencies_count": "Dependencies",
        "team_size": "Team Size",
        "completion_pct": "Completion %",
        "strategic_priority": "Strategic Priority",
    }
    return (
        pd.DataFrame({"feature": FEATURES, "importance": importances})
        .assign(label=lambda d: d["feature"].map(labels))
        .sort_values("importance", ascending=True)
    )


def flag_risk_divergence(projects_with_preds: pd.DataFrame) -> pd.DataFrame:
    risk_num = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
    df = projects_with_preds.copy()
    df["risk_num_actual"] = df["risk_level"].map(risk_num)
    df["risk_num_predicted"] = df["predicted_risk_level"].map(risk_num)
    df["risk_divergence"] = df["risk_num_predicted"] - df["risk_num_actual"]
    return df[df["risk_divergence"] != 0].sort_values("risk_divergence", ascending=False)


def compute_risk_trend(monthly_metrics: pd.DataFrame) -> pd.DataFrame:
    return (
        monthly_metrics
        .groupby("month")["risk_score"]
        .agg(["mean", "median", "max", "count"])
        .reset_index()
        .rename(columns={"mean": "avg_risk", "median": "median_risk", "max": "max_risk", "count": "n_projects"})
    )


def department_risk_summary(projects: pd.DataFrame) -> pd.DataFrame:
    return (
        projects.groupby("department").agg(
            avg_risk=("risk_score", "mean"),
            critical_count=("risk_level", lambda x: (x == "Critical").sum()),
            high_count=("risk_level", lambda x: (x == "High").sum()),
            at_risk_pct=("status", lambda x: (x.isin(["At Risk", "Off Track"])).mean() * 100),
            total_projects=("project_id", "count"),
            total_budget_at_risk=(
                "estimated_budget",
                lambda x: x[projects.loc[x.index, "status"].isin(["At Risk", "Off Track"])].sum(),
            ),
        )
        .reset_index()
        .round(1)
    )
