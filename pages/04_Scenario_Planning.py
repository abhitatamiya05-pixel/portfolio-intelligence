import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from scipy.optimize import linprog

from src.data_loader import load_data, apply_chart_theme, fmt_currency, STATUS_COLORS, RISK_COLORS, DEPT_COLORS
from src.risk_model import train_risk_model, predict_risk

st.set_page_config(page_title="Scenario Planning", page_icon="🔭", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .section-header { font-size: 1.05rem; font-weight: 600; color: #1E293B;
                      border-bottom: 2px solid #E2E8F0; padding-bottom: 0.4rem;
                      margin: 1.2rem 0 0.8rem; }
    .scenario-panel { background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px;
                      padding:1rem 1.2rem; }
    .result-good { color:#10B981; font-weight:700; }
    .result-bad { color:#EF4444; font-weight:700; }
</style>
""", unsafe_allow_html=True)

data = load_data()
projects = data["projects"]

st.markdown("## Scenario Planning & Portfolio Optimization")
st.caption("What-if analysis, portfolio optimizer, and trade-off simulation")

@st.cache_resource(show_spinner=False)
def get_model(n: int):
    return train_risk_model(projects)

model, le = get_model(len(projects))

tab1, tab2, tab3 = st.tabs([
    "📊  Portfolio Optimizer",
    "🔬  Project Risk Simulator",
    "⚖️  Portfolio Trade-Off Analysis",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Portfolio Optimizer
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### Portfolio Optimizer — Maximize Value Within Budget")
    st.markdown(
        "The optimizer selects the subset of projects that maximizes total **business value** "
        "subject to a budget constraint, using a greedy value-density algorithm. "
        "Filter by department or status before optimizing."
    )

    col_ctrl, col_res = st.columns([1, 1.6])

    with col_ctrl:
        st.markdown('<div class="section-header">Optimizer Controls</div>', unsafe_allow_html=True)

        opt_depts = st.multiselect("Departments to include", sorted(projects["department"].unique()),
                                    default=sorted(projects["department"].unique()), key="opt_depts")
        opt_status = st.multiselect("Include status", ["On Track", "At Risk", "Off Track", "On Hold"],
                                     default=["On Track", "At Risk", "On Hold"], key="opt_status")
        opt_min_priority = st.slider("Min strategic priority", 1, 5, 1, key="opt_prio")
        max_risk = st.slider("Max risk score allowed", 0, 100, 100, key="opt_risk")

        total_available = projects[projects["status"].isin(opt_status)]["estimated_budget"].sum()
        budget_cap = st.slider(
            "Budget cap ($M)",
            min_value=10.0,
            max_value=float(total_available / 1e6),
            value=float(total_available / 1e6 * 0.70),
            step=5.0,
            format="$%.0fM",
            key="opt_budget",
        )

        force_include_ids = []
        force_in = st.multiselect(
            "Force-include projects (by ID)",
            options=projects["project_id"].tolist(),
            default=[],
            key="force_include",
        )

        run_opt = st.button("▶  Run Optimization", type="primary", use_container_width=True)

    with col_res:
        if run_opt or "opt_result" in st.session_state:
            candidates = projects[
                projects["department"].isin(opt_depts)
                & projects["status"].isin(opt_status)
                & (projects["strategic_priority"] >= opt_min_priority)
                & (projects["risk_score"] <= max_risk)
            ].copy()

            forced = candidates[candidates["project_id"].isin(force_in)]
            forced_budget = forced["estimated_budget"].sum()
            remaining_budget = budget_cap * 1e6 - forced_budget

            not_forced = candidates[~candidates["project_id"].isin(force_in)].copy()
            not_forced["value_density"] = not_forced["business_value_score"] / (not_forced["estimated_budget"] / 1e6)
            not_forced = not_forced.sort_values("value_density", ascending=False)

            selected = []
            budget_used = 0.0
            for _, row in not_forced.iterrows():
                if budget_used + row["estimated_budget"] <= remaining_budget:
                    selected.append(row)
                    budget_used += row["estimated_budget"]

            result_df = pd.concat([forced, pd.DataFrame(selected)], ignore_index=True) if selected else forced

            excluded_df = candidates[~candidates["project_id"].isin(result_df["project_id"])]

            total_val = result_df["business_value_score"].sum()
            total_budget_used = result_df["estimated_budget"].sum()
            baseline_val = candidates["business_value_score"].sum()

            st.markdown('<div class="section-header">Optimization Results</div>', unsafe_allow_html=True)
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Projects Selected", len(result_df), f"of {len(candidates)}")
            r2.metric("Budget Used", fmt_currency(total_budget_used),
                      f"of {fmt_currency(budget_cap * 1e6)} cap")
            r3.metric("Total Business Value", f"{total_val:,}", f"vs {baseline_val:,} unconstrained")
            r4.metric("Value Capture Rate", f"{total_val/max(baseline_val,1)*100:.0f}%")

            st.session_state["opt_result"] = result_df

            # Comparison chart
            comp_data = pd.DataFrame({
                "Scenario": ["Unconstrained Portfolio", "Optimized Portfolio"],
                "Total Business Value": [baseline_val, total_val],
                "Budget ($M)": [candidates["estimated_budget"].sum() / 1e6, total_budget_used / 1e6],
                "Project Count": [len(candidates), len(result_df)],
            })

            fig = px.bar(comp_data, x="Scenario", y="Total Business Value",
                         color="Scenario", color_discrete_sequence=["#94A3B8", "#2563EB"],
                         text="Total Business Value")
            fig.update_traces(texttemplate="%{y:,}", textposition="outside", showlegend=False)
            apply_chart_theme(fig, height=280)
            st.plotly_chart(fig, use_container_width=True)

            # Selected projects table
            st.markdown("**Selected projects**")
            sel_display = result_df[["project_id", "project_name", "department", "strategic_priority",
                                      "business_value_score", "risk_level", "estimated_budget"]]\
                .rename(columns={"project_id": "ID", "project_name": "Project", "department": "Dept",
                                  "strategic_priority": "Priority", "business_value_score": "BV Score",
                                  "risk_level": "Risk", "estimated_budget": "Budget"})\
                .sort_values("BV Score", ascending=False)

            st.dataframe(sel_display, use_container_width=True, height=320)

            if len(excluded_df) > 0:
                with st.expander(f"View {len(excluded_df)} excluded projects"):
                    exc = excluded_df[["project_id", "project_name", "department",
                                        "business_value_score", "estimated_budget"]]\
                        .rename(columns={"project_id": "ID", "project_name": "Project",
                                          "department": "Dept", "business_value_score": "BV Score",
                                          "estimated_budget": "Budget"})\
                        .sort_values("BV Score", ascending=False)
                    st.dataframe(exc, use_container_width=True, height=240)
        else:
            st.info("Configure parameters on the left and click **Run Optimization** to see results.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Project Risk Simulator
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### Project Risk Simulator — Adjust Parameters & See Impact")
    st.markdown(
        "Select a project and adjust its key parameters to see how the ML model predicts "
        "its risk level and score would change. Useful for evaluating interventions."
    )

    active = projects[projects["status"] != "Completed"].copy()

    sim_col1, sim_col2, sim_col3 = st.columns([1.2, 1.2, 1.6])

    with sim_col1:
        st.markdown('<div class="section-header">Select Project</div>', unsafe_allow_html=True)
        sel_dept_sim = st.selectbox("Department", ["All"] + sorted(active["department"].unique()),
                                     key="sim_dept")
        proj_pool = active if sel_dept_sim == "All" else active[active["department"] == sel_dept_sim]
        sel_proj = st.selectbox("Project", proj_pool["project_name"].tolist(), key="sim_proj")

        proj_row = proj_pool[proj_pool["project_name"] == sel_proj].iloc[0]

        st.markdown("**Current State**")
        st.markdown(f"- **Risk Level:** {proj_row['risk_level']}")
        st.markdown(f"- **Risk Score:** {proj_row['risk_score']:.0f}/100")
        st.markdown(f"- **Status:** {proj_row['status']}")
        st.markdown(f"- **Budget Variance:** {proj_row['budget_variance_pct']:+.1f}%")
        st.markdown(f"- **Schedule Slip:** {proj_row['schedule_variance_days']:+d} days")

    with sim_col2:
        st.markdown('<div class="section-header">Adjust Scenario Parameters</div>', unsafe_allow_html=True)

        new_budget_var = st.slider("Budget Variance %", -20.0, 80.0,
                                    float(proj_row["budget_variance_pct"]), 1.0, key="sim_bv")
        new_schedule = st.slider("Schedule Variance (days)", -30, 180,
                                  int(proj_row["schedule_variance_days"]), 5, key="sim_sv")
        new_issues = st.slider("Open Issues", 0, 50, int(proj_row["issue_count"]), 1, key="sim_issues")
        new_critical = st.slider("Critical Issues", 0, min(new_issues, 15), int(min(proj_row["critical_issues"], new_issues)), 1, key="sim_crit")
        new_cr = st.slider("Change Requests", 0, 30, int(proj_row["change_requests"]), 1, key="sim_cr")
        new_team = st.slider("Team Size", 1, 30, int(proj_row["team_size"]), 1, key="sim_team")
        new_complexity = st.slider("Complexity (1-5)", 1, 5, int(proj_row["complexity_score"]), 1, key="sim_complexity")
        new_deps = st.slider("Dependencies", 0, 15, int(proj_row["dependencies_count"]), 1, key="sim_deps")

    with sim_col3:
        st.markdown('<div class="section-header">Risk Prediction Result</div>', unsafe_allow_html=True)

        from src.risk_model import FEATURES
        sim_input = pd.DataFrame([{
            "budget_variance_pct": new_budget_var,
            "schedule_variance_days": new_schedule,
            "issue_count": new_issues,
            "critical_issues": new_critical,
            "change_requests": new_cr,
            "complexity_score": new_complexity,
            "dependencies_count": new_deps,
            "team_size": new_team,
            "completion_pct": proj_row["completion_pct"],
            "strategic_priority": proj_row["strategic_priority"],
        }])

        sim_pred = model.predict(sim_input.values)[0]
        sim_probs = model.predict_proba(sim_input.values)[0]
        sim_risk_label = le.inverse_transform([sim_pred])[0]
        sim_risk_score = (sim_probs[le.transform(["Low"])[0]] * 12.5 +
                          sim_probs[le.transform(["Medium"])[0]] * 37.5 +
                          sim_probs[le.transform(["High"])[0]] * 62.5 +
                          sim_probs[le.transform(["Critical"])[0]] * 87.5)

        original_score = proj_row["risk_score"]
        delta_score = sim_risk_score - original_score
        color = {"Low": "#10B981", "Medium": "#F59E0B", "High": "#F97316", "Critical": "#EF4444"}.get(sim_risk_label, "#64748B")

        st.markdown(f"""
        <div style="background:{color}15;border:2px solid {color};border-radius:12px;
                    padding:1.5rem;text-align:center;margin-bottom:1rem;">
            <div style="font-size:0.85rem;color:#64748B;text-transform:uppercase;letter-spacing:0.05em;">
                Predicted Risk Level</div>
            <div style="font-size:2.5rem;font-weight:800;color:{color};margin:0.3rem 0;">
                {sim_risk_label}</div>
            <div style="font-size:1.5rem;font-weight:700;color:#1E293B;">
                {sim_risk_score:.0f}<span style="font-size:1rem;color:#64748B;">/100</span></div>
            <div style="font-size:0.9rem;color:{'#EF4444' if delta_score > 0 else '#10B981'};
                        font-weight:600;margin-top:0.4rem;">
                {'▲' if delta_score > 0 else '▼'} {abs(delta_score):.1f} vs current
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Probability breakdown
        risk_labels = le.classes_
        prob_df = pd.DataFrame({
            "Risk Level": [le.inverse_transform([i])[0] for i in range(len(risk_labels))],
            "Probability": sim_probs * 100,
        })
        fig_prob = px.bar(
            prob_df, x="Risk Level", y="Probability", color="Risk Level",
            color_discrete_map=RISK_COLORS,
            text=prob_df["Probability"].map("{:.0f}%".format),
            labels={"Probability": "Probability %"},
        )
        fig_prob.update_traces(textposition="outside", showlegend=False)
        apply_chart_theme(fig_prob, height=240)
        fig_prob.update_layout(margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_prob, use_container_width=True)

        delta_bv = new_budget_var - proj_row["budget_variance_pct"]
        delta_sched = new_schedule - proj_row["schedule_variance_days"]
        budget_cost = proj_row["estimated_budget"] * delta_bv / 100
        st.markdown(f"**Financial impact of changes:**")
        st.markdown(f"- Budget variance change: **{delta_bv:+.1f}%** → {fmt_currency(abs(budget_cost))} {'overrun' if budget_cost > 0 else 'saving'}")
        st.markdown(f"- Schedule variance change: **{delta_sched:+d} days**")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Portfolio Trade-Off Analysis
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### Portfolio Trade-Off Analysis")
    st.markdown(
        "Visualize how the portfolio's risk-value trade-off compares across scenarios. "
        "Identify projects that are 'worth the risk' vs those that dilute portfolio quality."
    )

    c_t1, c_t2 = st.columns([1, 1])

    with c_t1:
        st.markdown('<div class="section-header">Value/Risk Quadrant Analysis</div>', unsafe_allow_html=True)

        active_p = projects[projects["status"] != "Completed"].copy()
        avg_value = active_p["business_value_score"].mean()
        avg_risk = active_p["risk_score"].mean()

        active_p["quadrant"] = "Monitor"
        active_p.loc[(active_p["business_value_score"] >= avg_value) & (active_p["risk_score"] < avg_risk), "quadrant"] = "Stars (High Value, Low Risk)"
        active_p.loc[(active_p["business_value_score"] >= avg_value) & (active_p["risk_score"] >= avg_risk), "quadrant"] = "Strategic Bets (High Value, High Risk)"
        active_p.loc[(active_p["business_value_score"] < avg_value) & (active_p["risk_score"] >= avg_risk), "quadrant"] = "Candidates for Review"
        active_p.loc[(active_p["business_value_score"] < avg_value) & (active_p["risk_score"] < avg_risk), "quadrant"] = "Low Priority"

        quadrant_colors = {
            "Stars (High Value, Low Risk)": "#10B981",
            "Strategic Bets (High Value, High Risk)": "#F59E0B",
            "Candidates for Review": "#EF4444",
            "Low Priority": "#94A3B8",
        }

        fig_q = px.scatter(
            active_p, x="risk_score", y="business_value_score",
            color="quadrant", size="estimated_budget",
            color_discrete_map=quadrant_colors,
            hover_name="project_name",
            hover_data={"department": True, "status": True, "estimated_budget": ":$,.0f",
                        "project_manager": True},
            size_max=25,
            labels={"risk_score": "Risk Score", "business_value_score": "Business Value"},
        )
        fig_q.add_vline(x=avg_risk, line_dash="dot", line_color="#64748B")
        fig_q.add_hline(y=avg_value, line_dash="dot", line_color="#64748B")
        apply_chart_theme(fig_q, height=400)
        st.plotly_chart(fig_q, use_container_width=True)

        quadrant_summary = active_p["quadrant"].value_counts().reset_index()
        quadrant_summary.columns = ["Quadrant", "Count"]
        budget_by_q = active_p.groupby("quadrant")["estimated_budget"].sum().reset_index()
        budget_by_q.columns = ["Quadrant", "Total Budget"]
        quadrant_summary = quadrant_summary.merge(budget_by_q, on="Quadrant")
        quadrant_summary["Total Budget"] = quadrant_summary["Total Budget"].apply(fmt_currency)
        st.dataframe(quadrant_summary, use_container_width=True, height=200)

    with c_t2:
        st.markdown('<div class="section-header">Department Portfolio Efficiency</div>', unsafe_allow_html=True)

        dept_eff = active_p.groupby("department").agg(
            avg_value=("business_value_score", "mean"),
            avg_risk=("risk_score", "mean"),
            total_budget=("estimated_budget", "sum"),
            project_count=("project_id", "count"),
            value_per_dollar=("business_value_score", "sum"),
        ).reset_index()
        dept_eff["value_per_million"] = dept_eff["avg_value"] / (dept_eff["total_budget"] / 1e6)
        dept_eff["efficiency_score"] = (dept_eff["avg_value"] / dept_eff["avg_risk"].replace(0, 1)).round(2)

        fig_eff = px.scatter(
            dept_eff,
            x="avg_risk", y="avg_value",
            size="total_budget", color="department",
            color_discrete_map=DEPT_COLORS,
            text="department",
            hover_data={"total_budget": ":$,.0f", "project_count": True, "efficiency_score": ":.2f"},
            size_max=50,
            labels={"avg_risk": "Avg Risk Score", "avg_value": "Avg Business Value"},
        )
        fig_eff.update_traces(textposition="top center")
        apply_chart_theme(fig_eff, height=340)
        st.plotly_chart(fig_eff, use_container_width=True)

        st.markdown('<div class="section-header">Portfolio Efficiency Leaderboard</div>', unsafe_allow_html=True)
        eff_display = dept_eff[["department", "avg_value", "avg_risk", "efficiency_score",
                                  "total_budget", "project_count"]]\
            .rename(columns={"department": "Department", "avg_value": "Avg BV",
                              "avg_risk": "Avg Risk", "efficiency_score": "Efficiency Ratio",
                              "total_budget": "Total Budget", "project_count": "Projects"})\
            .sort_values("Efficiency Ratio", ascending=False)

        st.dataframe(eff_display, use_container_width=True, height=250)

        st.info(
            "**Efficiency Ratio** = Avg Business Value ÷ Avg Risk Score. "
            "Higher is better — departments with high value projects running at lower risk "
            "have stronger portfolio efficiency."
        )
