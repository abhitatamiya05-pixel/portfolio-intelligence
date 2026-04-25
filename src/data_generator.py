import numpy as np
import pandas as pd
from datetime import date, timedelta
import random

SEED = 42
TODAY = date(2025, 4, 25)

DEPT_COUNTS = {
    "IT": 60, "Operations": 45, "Finance": 35,
    "Marketing": 40, "Product": 45, "HR": 25,
}

PROGRAMS = {
    "IT": ["Cloud Migration", "Cybersecurity", "ERP Modernization", "Data Platform", "Digital Infrastructure"],
    "Operations": ["Process Excellence", "Supply Chain", "Lean Transformation", "Quality Management"],
    "Finance": ["Financial Systems", "Compliance & Controls", "Cost Reduction", "Treasury Management"],
    "Marketing": ["Brand Strategy", "Digital Growth", "Customer Experience", "Market Expansion"],
    "Product": ["Platform Innovation", "Product Lifecycle", "Customer Success", "API Ecosystem"],
    "HR": ["Talent Transformation", "HRIS Upgrade", "Culture & Engagement", "Workforce Planning"],
}

NAME_POOL = {
    "IT": [
        "Cloud Infrastructure Migration", "Cybersecurity Framework Deployment",
        "ERP System Modernization", "Data Platform Architecture", "Network Redesign Initiative",
        "Identity & Access Management", "DevOps Pipeline Automation", "API Gateway Implementation",
        "Disaster Recovery Enhancement", "Zero-Trust Security Program", "SaaS Application Migration",
        "Digital Workplace Transformation", "ITSM Tool Upgrade", "Container Platform Rollout",
        "AI/ML Infrastructure Build", "Data Lake Implementation", "Hybrid Cloud Optimization",
        "Legacy System Retirement", "Endpoint Security Modernization", "Real-Time Analytics Platform",
        "Data Center Consolidation", "IoT Platform Development", "Microservices Architecture Migration",
        "Database Modernization Program", "Business Intelligence Refresh", "Observability Platform",
        "Automation Center of Excellence", "Low-Code Platform Deployment", "Digital Twin Initiative",
        "Blockchain Proof of Concept", "Edge Computing Infrastructure", "5G Network Readiness",
    ],
    "Operations": [
        "Process Automation Initiative", "Supply Chain Visibility Platform", "Lean Manufacturing Rollout",
        "Quality Management System Upgrade", "Warehouse Management Optimization", "Procurement Digitization",
        "Operational Risk Framework", "Continuous Improvement Program", "Asset Management System",
        "Vendor Portal Implementation", "Field Operations Digitization", "Logistics Route Optimization",
        "Capacity Planning Tool", "Demand Forecasting Platform", "Operational Analytics Dashboard",
        "Compliance Monitoring System", "Environmental Reporting Platform", "Cost Reduction Program",
        "Safety Management Platform", "Facilities Management System", "Returns Management Automation",
    ],
    "Finance": [
        "Financial Consolidation System", "Regulatory Compliance Overhaul", "Tax Automation Platform",
        "Treasury Management Upgrade", "Accounts Payable Automation", "FP&A Tool Implementation",
        "Audit Management System", "Revenue Recognition Platform", "Cost Accounting Modernization",
        "Cash Flow Forecasting Tool", "Enterprise Risk Management Framework", "Internal Controls Automation",
        "Financial Data Warehouse", "Expense Management System", "Budgeting & Forecasting Platform",
        "Transfer Pricing System", "SOX Compliance Program", "Financial Close Acceleration",
        "Intercompany Reconciliation Tool", "Lease Accounting System",
    ],
    "Marketing": [
        "Marketing Automation Platform", "Customer Data Platform", "Brand Identity Refresh",
        "Digital Campaign Analytics", "CRM Enhancement Program", "Content Management System",
        "E-commerce Platform Upgrade", "Customer Loyalty Program", "Market Research Platform",
        "Social Media Intelligence", "Personalization Engine", "Marketing Attribution System",
        "Campaign Management Tool", "Customer Segmentation Platform", "Influencer Marketing Program",
        "SEO & SEM Optimization Platform", "Customer Journey Mapping", "Product Launch Framework",
        "Regional Market Expansion", "Competitive Intelligence System", "Voice of Customer Program",
    ],
    "Product": [
        "Next-Gen Product Platform", "Mobile App Rewrite", "API Ecosystem Development",
        "Product Analytics Platform", "Customer Feedback System", "Feature Flagging Infrastructure",
        "A/B Testing Platform", "User Research Program", "Product Roadmap Tool",
        "Subscription Management System", "Dynamic Pricing Engine", "Recommendation System Build",
        "Search Platform Upgrade", "Notification Infrastructure", "Data Privacy Compliance Program",
        "Performance Optimization Initiative", "Multi-Region Deployment", "Accessibility Program",
        "Integration Platform Build", "Developer Experience Platform", "SDK & Documentation Portal",
    ],
    "HR": [
        "HRIS Platform Upgrade", "Talent Acquisition System", "Learning Management System",
        "Performance Management Redesign", "Employee Self-Service Portal", "Payroll System Migration",
        "Succession Planning Platform", "Employee Experience Initiative", "DEI Program Launch",
        "Workforce Analytics Platform", "Onboarding Automation", "Compensation Benchmarking Tool",
        "HR Chatbot Implementation", "Benefits Management System", "Time & Attendance Upgrade",
        "Leadership Development Program", "Skills Taxonomy Build", "HR Shared Services Setup",
    ],
}

PROJECT_MANAGERS = [
    "Sarah Chen", "Marcus Johnson", "Priya Patel", "David Thompson", "Jessica Williams",
    "Robert Kim", "Amanda Rodriguez", "James O'Brien", "Natasha Singh", "Michael Brown",
    "Lauren Davis", "Carlos Mendez", "Emily Watson", "Kevin Nguyen", "Rachel Foster",
    "Daniel Park", "Samantha Hughes", "Christopher Lee",
]

SPONSORS = [
    "Alan Marsh (VP Technology)", "Sandra Wu (CIO)", "Peter Blackwell (CFO)",
    "Diana Torres (CMO)", "Frank Henderson (COO)", "Michelle Adams (CHRO)",
    "Ryan Cole (SVP Product)", "Barbara Knight (SVP Operations)",
    "Thomas Grant (SVP Finance)", "Richard Hartley (CEO)",
]

DEPT_SPONSORS = {
    "IT": ["Alan Marsh (VP Technology)", "Sandra Wu (CIO)"],
    "Finance": ["Peter Blackwell (CFO)", "Thomas Grant (SVP Finance)"],
    "Marketing": ["Diana Torres (CMO)"],
    "Operations": ["Frank Henderson (COO)", "Barbara Knight (SVP Operations)"],
    "HR": ["Michelle Adams (CHRO)"],
    "Product": ["Ryan Cole (SVP Product)", "Richard Hartley (CEO)"],
}

RESOURCE_ROLES = [
    "Project Manager", "Business Analyst", "Solution Architect", "Senior Developer",
    "Developer", "Data Engineer", "Data Scientist", "QA Engineer", "UX Designer",
    "Change Manager", "Scrum Master", "DevOps Engineer", "Security Analyst", "PMO Analyst",
]

RESOURCE_NAMES = [
    ("Alex", "Anderson"), ("Jordan", "Baker"), ("Taylor", "Carter"), ("Morgan", "Davis"),
    ("Casey", "Evans"), ("Riley", "Foster"), ("Avery", "Garcia"), ("Quinn", "Hill"),
    ("Blake", "Jackson"), ("Cameron", "Johnson"), ("Drew", "Kelly"), ("Finley", "Lee"),
    ("Harper", "Martin"), ("Hayden", "Miller"), ("Jamie", "Moore"), ("Jesse", "Nelson"),
    ("Kelly", "Parker"), ("Logan", "Price"), ("Mackenzie", "Roberts"), ("Madison", "Scott"),
    ("Parker", "Smith"), ("Peyton", "Taylor"), ("Reagan", "Thomas"), ("Reese", "Turner"),
    ("Ryan", "Walker"), ("Sage", "White"), ("Skylar", "Williams"), ("Spencer", "Wilson"),
    ("Sydney", "Young"), ("Tyler", "Zhang"), ("Whitney", "Brown"), ("Bailey", "Chen"),
    ("Brett", "Clark"), ("Chandler", "Cooper"), ("Dallas", "Cruz"), ("Devon", "Diaz"),
    ("Dominique", "Edwards"), ("Ellis", "Flores"), ("Emerson", "Gonzalez"), ("Evan", "Gray"),
    ("Gray", "Harris"), ("Hunter", "Hernandez"), ("Ivory", "Jones"), ("Jade", "King"),
    ("Kai", "Lewis"), ("Lane", "Lopez"), ("Lee", "Mason"), ("Lennon", "Nguyen"),
    ("Leslie", "Patel"), ("London", "Perez"), ("Marcus", "Reed"), ("Merritt", "Rivera"),
    ("Monroe", "Robinson"), ("Nash", "Rodriguez"), ("Noel", "Sanchez"), ("Nova", "Stewart"),
    ("Page", "Thompson"), ("Phoenix", "Torres"), ("Piper", "Wright"), ("Robin", "Adams"),
    ("Rowan", "Allen"), ("Sam", "Butler"), ("Sterling", "Campbell"), ("Tristan", "Collins"),
    ("Umber", "Cook"), ("Vale", "Cox"),
]

NAME_SUFFIXES = [
    "", " Phase 2", " - Global Rollout", " v2.0", " Refresh",
    " Enhancement", " - APAC", " Optimization", " - Enterprise", "",
]


def generate_all_data(seed: int = SEED) -> dict[str, pd.DataFrame]:
    np.random.seed(seed)
    random.seed(seed)

    projects = _generate_projects()
    resources = _generate_resources()
    allocations = _generate_allocations(projects, resources)
    dependencies = _generate_dependencies(projects)
    monthly_metrics = _generate_monthly_metrics(projects)

    return {
        "projects": projects,
        "resources": resources,
        "allocations": allocations,
        "dependencies": dependencies,
        "monthly_metrics": monthly_metrics,
    }


def _generate_projects() -> pd.DataFrame:
    rows = []
    counter = 1

    for dept, count in DEPT_COUNTS.items():
        name_pool = NAME_POOL[dept].copy()
        used_suffixes: dict[str, int] = {}

        for _ in range(count):
            pid = f"PROJ-{counter:04d}"
            counter += 1

            base_name = random.choice(name_pool)
            suffix_idx = used_suffixes.get(base_name, 0)
            if suffix_idx == 0:
                project_name = base_name
            else:
                project_name = base_name + NAME_SUFFIXES[min(suffix_idx, len(NAME_SUFFIXES) - 1)]
            used_suffixes[base_name] = suffix_idx + 1

            program = random.choice(PROGRAMS[dept])
            pm = random.choice(PROJECT_MANAGERS)
            sponsor = random.choice(DEPT_SPONSORS.get(dept, SPONSORS))

            strategic_priority = int(np.random.choice([1, 2, 3, 4, 5], p=[0.08, 0.18, 0.35, 0.27, 0.12]))
            business_value_score = int(np.clip(strategic_priority * 14 + np.random.normal(10, 8), 10, 100))
            complexity_score = int(np.random.choice([1, 2, 3, 4, 5], p=[0.10, 0.22, 0.35, 0.23, 0.10]))

            size_probs = {1: [0.55, 0.30, 0.12, 0.03], 2: [0.40, 0.38, 0.17, 0.05],
                         3: [0.25, 0.38, 0.27, 0.10], 4: [0.12, 0.30, 0.38, 0.20],
                         5: [0.08, 0.20, 0.42, 0.30]}
            size_cat = str(np.random.choice(["Small", "Medium", "Large", "Very Large"],
                                            p=size_probs[complexity_score]))

            budget_ranges = {
                "Small": (50_000, 500_000), "Medium": (500_000, 2_000_000),
                "Large": (2_000_000, 10_000_000), "Very Large": (10_000_000, 45_000_000),
            }
            lo, hi = budget_ranges[size_cat]
            estimated_budget = round(float(np.random.uniform(lo, hi)), -3)

            duration_map = {
                "Small": (30, 150), "Medium": (90, 365),
                "Large": (180, 548), "Very Large": (300, 730),
            }
            d_lo, d_hi = duration_map[size_cat]
            duration_days = random.randint(d_lo, d_hi)

            start_offset = random.randint(-540, 120)
            planned_start = TODAY + timedelta(days=start_offset)
            planned_end = planned_start + timedelta(days=duration_days)
            pct_through = (TODAY - planned_start).days / max(duration_days, 1)

            if planned_start > TODAY:
                status = str(np.random.choice(["On Track", "On Hold"], p=[0.92, 0.08]))
                phase = "Initiation"
                completion_pct = random.randint(0, 5)
            elif planned_end < TODAY - timedelta(days=21):
                status = str(np.random.choice(["Completed", "Off Track", "At Risk"], p=[0.68, 0.22, 0.10]))
                phase = "Closure"
                completion_pct = 100 if status == "Completed" else random.randint(72, 94)
            else:
                status = str(np.random.choice(
                    ["On Track", "At Risk", "Off Track", "On Hold"],
                    p=[0.38, 0.33, 0.17, 0.12],
                ))
                if pct_through < 0.12:
                    phase = "Initiation"
                    completion_pct = random.randint(0, 12)
                elif pct_through < 0.28:
                    phase = "Planning"
                    completion_pct = random.randint(10, 28)
                elif pct_through < 0.72:
                    phase = "Execution"
                    target = int(pct_through * 100)
                    delta = -15 if status in ["At Risk", "Off Track"] else 5
                    completion_pct = int(np.clip(target + delta + random.randint(-8, 8), 5, 95))
                else:
                    phase = "Monitoring & Control"
                    target = int(pct_through * 95)
                    delta = -20 if status in ["At Risk", "Off Track"] else 3
                    completion_pct = int(np.clip(target + delta + random.randint(-5, 5), 35, 98))

            team_size_base = {"Small": 3, "Medium": 7, "Large": 13, "Very Large": 22}
            team_size = max(2, int(team_size_base[size_cat] + np.random.normal(0, team_size_base[size_cat] * 0.25)))
            stakeholder_count = max(3, int(team_size * 1.4 + np.random.normal(0, 3)))

            issue_base = complexity_score * 2.5 + (6 if status in ["At Risk", "Off Track"] else 0)
            issue_count = max(0, int(np.random.poisson(issue_base)))
            critical_issues = max(0, min(issue_count, int(np.random.poisson(max(0.1, issue_count * 0.18)))))
            change_requests = max(0, int(np.random.poisson(complexity_score * 1.8)))
            dependencies_count = max(0, int(np.random.poisson(complexity_score * 0.9)))

            schedule_var = {
                "On Track": random.randint(-8, 12),
                "At Risk": random.randint(8, 50),
                "Off Track": random.randint(35, 130),
                "Completed": random.randint(-15, 65),
                "On Hold": random.randint(12, 90),
            }
            schedule_variance_days = schedule_var[status]

            start_delay = max(0, random.randint(-3, 18))
            actual_start = planned_start + timedelta(days=start_delay)
            if actual_start > TODAY:
                actual_start = planned_start
            forecast_end = planned_end + timedelta(days=schedule_variance_days)

            bv_base_by_status = {
                "On Track": np.random.normal(2, 4),
                "At Risk": np.random.normal(14, 7),
                "Off Track": np.random.normal(28, 12),
                "Completed": np.random.normal(6, 14),
                "On Hold": np.random.normal(10, 8),
            }
            budget_variance_pct = round(float(bv_base_by_status[status]) + (complexity_score - 3) * 2.5, 1)

            forecast_at_completion = round(estimated_budget * (1 + budget_variance_pct / 100), -2)
            actual_spend_ytd = round(
                min(estimated_budget * (completion_pct / 100) * (1 + budget_variance_pct / 200),
                    forecast_at_completion * 0.98),
                -2,
            )

            # Risk components (0-100 each)
            budget_risk = float(np.clip(budget_variance_pct * 2.2, 0, 100))
            schedule_risk = float(np.clip(schedule_variance_days * 1.1, 0, 100))
            issue_risk = float(np.clip(issue_count * 3.5 + critical_issues * 12, 0, 100))
            complexity_risk = float(complexity_score * 16)
            dependency_risk = float(np.clip(dependencies_count * 13, 0, 100))

            raw_risk = (
                0.25 * budget_risk
                + 0.25 * schedule_risk
                + 0.20 * issue_risk
                + 0.17 * complexity_risk
                + 0.13 * dependency_risk
            )
            status_adj = {"On Track": -8, "At Risk": 14, "Off Track": 26, "Completed": -18, "On Hold": 4}
            risk_score = round(float(np.clip(raw_risk + status_adj[status], 0, 100)), 1)

            if risk_score < 25:
                risk_level = "Low"
            elif risk_score < 50:
                risk_level = "Medium"
            elif risk_score < 75:
                risk_level = "High"
            else:
                risk_level = "Critical"

            risk_probability = round(float(np.clip(risk_score / 100 + np.random.normal(0, 0.07), 0.05, 0.95)), 2)
            impact_raw = (business_value_score / 100 * 0.6 + estimated_budget / 45_000_000 * 0.4)
            risk_impact = round(float(np.clip(impact_raw + np.random.normal(0, 0.08), 0.05, 1.0)), 2)

            health_index = round(float(np.clip(
                100 - risk_score * 0.55 - max(0, schedule_variance_days * 0.08) - max(0, budget_variance_pct * 0.28),
                0, 100,
            )), 1)

            if status == "Completed":
                benefits_realized_pct = random.randint(62, 100)
            elif status in ["Off Track", "On Hold"]:
                benefits_realized_pct = random.randint(0, 28)
            else:
                benefits_realized_pct = int(completion_pct * random.uniform(0.45, 0.85))

            last_updated = TODAY - timedelta(days=random.randint(0, 12))

            rows.append({
                "project_id": pid,
                "project_name": project_name,
                "department": dept,
                "program": program,
                "project_manager": pm,
                "sponsor": sponsor,
                "strategic_priority": strategic_priority,
                "business_value_score": business_value_score,
                "complexity_score": complexity_score,
                "size_category": size_cat,
                "estimated_budget": estimated_budget,
                "actual_spend_ytd": actual_spend_ytd,
                "forecast_at_completion": forecast_at_completion,
                "budget_variance_pct": budget_variance_pct,
                "planned_start_date": planned_start.strftime("%Y-%m-%d"),
                "planned_end_date": planned_end.strftime("%Y-%m-%d"),
                "actual_start_date": actual_start.strftime("%Y-%m-%d"),
                "forecast_end_date": forecast_end.strftime("%Y-%m-%d"),
                "schedule_variance_days": schedule_variance_days,
                "status": status,
                "phase": phase,
                "completion_pct": int(completion_pct),
                "issue_count": int(issue_count),
                "critical_issues": int(critical_issues),
                "change_requests": int(change_requests),
                "dependencies_count": int(dependencies_count),
                "team_size": int(team_size),
                "stakeholder_count": int(stakeholder_count),
                "risk_probability": risk_probability,
                "risk_impact": risk_impact,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "health_index": health_index,
                "benefits_realized_pct": int(benefits_realized_pct),
                "last_updated": last_updated.strftime("%Y-%m-%d"),
            })

    return pd.DataFrame(rows)


def _generate_resources() -> pd.DataFrame:
    rows = []
    name_pool = list(RESOURCE_NAMES)
    random.shuffle(name_pool)

    for i, (first, last) in enumerate(name_pool[:65]):
        rid = f"RES-{i+1:03d}"
        role = random.choice(RESOURCE_ROLES)
        dept = random.choice(list(DEPT_COUNTS.keys()))
        seniority = str(np.random.choice(
            ["Junior", "Mid", "Senior", "Lead", "Principal"],
            p=[0.15, 0.28, 0.35, 0.15, 0.07],
        ))

        capacity_map = {"Junior": 140, "Mid": 150, "Senior": 160, "Lead": 155, "Principal": 145}
        capacity = int(capacity_map[seniority] + np.random.normal(0, 8))

        cost_base = {"Junior": 75, "Mid": 110, "Senior": 145, "Lead": 175, "Principal": 210}
        role_adj = {
            "Solution Architect": 25, "Data Scientist": 20, "DevOps Engineer": 15,
            "Security Analyst": 18, "Project Manager": 10, "Developer": 5,
            "Senior Developer": 15, "PMO Analyst": -10, "QA Engineer": -5,
        }
        cost_per_hour = round(cost_base[seniority] + role_adj.get(role, 0) + np.random.normal(0, 8), 0)

        rows.append({
            "resource_id": rid,
            "resource_name": f"{first} {last}",
            "role": role,
            "department": dept,
            "seniority": seniority,
            "monthly_capacity_hours": capacity,
            "cost_per_hour": int(cost_per_hour),
        })

    return pd.DataFrame(rows)


def _generate_allocations(projects: pd.DataFrame, resources: pd.DataFrame) -> pd.DataFrame:
    """Generate allocations from the resource side: each resource is assigned
    to 1–6 projects per month with capacity distributed across them.
    ~22% of resources are intentionally overloaded to create interesting patterns."""
    rows = []
    alloc_id = 1

    # Build 6 proper first-of-month dates going backward from today
    _months = []
    y, m = TODAY.year, TODAY.month
    for _ in range(6):
        _months.append(date(y, m, 1))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    months = list(reversed(_months))

    active_pids = projects[projects["status"].isin(["On Track", "At Risk", "Off Track"])]["project_id"].tolist()
    res_capacity = resources.set_index("resource_id")["monthly_capacity_hours"].to_dict()

    for _, res in resources.iterrows():
        rid = res["resource_id"]
        capacity = res["monthly_capacity_hours"]
        is_overloaded = random.random() < 0.22

        for month in months:
            n_projects = random.randint(1, 6)
            assigned = random.sample(active_pids, min(n_projects, len(active_pids)))

            if is_overloaded:
                target_util = random.uniform(1.08, 1.40)
            else:
                target_util = random.uniform(0.55, 0.95)

            total_hours = capacity * target_util * (1 + random.uniform(-0.04, 0.04))

            # Distribute total hours across projects using Dirichlet split
            splits = np.random.dirichlet(np.ones(len(assigned)))

            for pid, split in zip(assigned, splits):
                hours = round(float(total_hours * split), 1)
                if hours < 4:
                    continue
                rows.append({
                    "allocation_id": f"ALLOC-{alloc_id:05d}",
                    "resource_id": rid,
                    "project_id": pid,
                    "month": month.strftime("%Y-%m"),
                    "allocated_hours": hours,
                })
                alloc_id += 1

    return pd.DataFrame(rows)


def _generate_dependencies(projects: pd.DataFrame) -> pd.DataFrame:
    rows = []
    dep_id = 1
    pids = projects["project_id"].tolist()
    dep_types = ["Finish-to-Start", "Start-to-Start", "Finish-to-Finish", "Data Dependency", "Technology Dependency"]

    for _, proj in projects.iterrows():
        n_deps = proj["dependencies_count"]
        if n_deps == 0:
            continue
        candidates = [p for p in pids if p != proj["project_id"]]
        chosen = random.sample(candidates, min(n_deps, len(candidates)))
        for dep_pid in chosen:
            rows.append({
                "dependency_id": f"DEP-{dep_id:04d}",
                "project_id": proj["project_id"],
                "depends_on_project_id": dep_pid,
                "dependency_type": random.choice(dep_types),
                "criticality": random.choice(["High", "High", "Medium", "Low"]),
            })
            dep_id += 1

    return pd.DataFrame(rows)


def _generate_monthly_metrics(projects: pd.DataFrame) -> pd.DataFrame:
    rows = []
    _m = []
    y, m = TODAY.year, TODAY.month
    for _ in range(6):
        _m.append(date(y, m, 1))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    months = list(reversed(_m))

    active = projects[projects["status"] != "Completed"].copy()

    for _, proj in active.iterrows():
        base_risk = proj["risk_score"]
        base_completion = proj["completion_pct"]
        base_issues = proj["issue_count"]

        for i, month in enumerate(months):
            month_ago = len(months) - 1 - i
            risk_then = float(np.clip(base_risk - (month_ago * random.uniform(-1.5, 3.5)), 0, 100))
            completion_then = max(0, int(base_completion - month_ago * random.uniform(3, 10)))
            issues_then = max(0, int(base_issues - month_ago * random.uniform(0, 2)))
            budget_util = round(float(np.clip(
                proj["actual_spend_ytd"] / max(proj["estimated_budget"], 1) * 100
                * (completion_then / max(base_completion, 1)), 0, 120
            )), 1)

            rows.append({
                "project_id": proj["project_id"],
                "month": month.strftime("%Y-%m"),
                "risk_score": round(risk_then, 1),
                "completion_pct": completion_then,
                "budget_utilization_pct": budget_util,
                "issue_count": issues_then,
            })

    return pd.DataFrame(rows)
