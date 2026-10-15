"""
Sprints Talent Analytics
Interactive Dashboard Generator

Generates a standalone HTML dashboard using:
- Python
- Pandas
- NumPy
- Plotly.js
- HTML and JavaScript

Input:
    data/sprints_cohort_features.csv
    data/employer_partner_requirements.json

Output:
    dashboard/index.html
"""

from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

LEARNER_DATA_PATH = (
    PROJECT_ROOT / "data" / "sprints_cohort_features.csv"
)

EMPLOYER_DATA_PATH = (
    PROJECT_ROOT / "data" / "employer_partner_requirements.json"
)

OUTPUT_PATH = (
    PROJECT_ROOT / "dashboard" / "index.html"
)


# ============================================================
# 2. DATA LOADING
# ============================================================

def load_learner_data():
    """Load and validate the learner dataset."""

    if not LEARNER_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Learner dataset not found: {LEARNER_DATA_PATH}"
        )

    df = pd.read_csv(LEARNER_DATA_PATH)

    required_columns = [
        "learner_id",
        "cohort_id",
        "track_name",
        "engagement_score",
        "average_module_score",
        "capstone_score",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required learner columns: "
            + ", ".join(missing_columns)
        )

    if df.empty:
        raise ValueError("The learner dataset is empty.")

    # Convert score columns to numeric without modifying the source file.
    score_columns = [
        column
        for column in df.columns
        if column.endswith("_score")
    ]

    for column in score_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    return df


def load_employer_data():
    """Load and validate employer requirements."""

    if not EMPLOYER_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Employer requirements not found: "
            f"{EMPLOYER_DATA_PATH}"
        )

    with open(
        EMPLOYER_DATA_PATH,
        "r",
        encoding="utf-8"
    ) as file:
        data = json.load(file)

    roles = data.get("employer_requirements")

    if not isinstance(roles, list):
        raise ValueError(
            "Expected 'employer_requirements' to be a list."
        )

    if not roles:
        raise ValueError(
            "No employer requirements were found."
        )

    employer_df = pd.DataFrame(roles)

    required_columns = [
        "role_id",
        "job_title",
        "company_tier",
        "required_skills",
        "minimum_assessment_threshold",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in employer_df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required employer columns: "
            + ", ".join(missing_columns)
        )

    return employer_df


# ============================================================
# 3. DATA PREPARATION
# ============================================================

def prepare_dashboard_data(learners, employers):
    """Prepare JSON-compatible data for the HTML dashboard."""

    # --------------------------------------------------------
    # Assessment columns
    # --------------------------------------------------------

    module_columns = [
        f"module_{number}_score"
        for number in range(1, 11)
        if f"module_{number}_score" in learners.columns
    ]

    assessment_columns = (
        module_columns + ["capstone_score"]
    )

    assessment_labels = [
        f"Module {number}"
        for number in range(1, 11)
        if f"module_{number}_score" in learners.columns
    ]

    assessment_labels.append("Capstone")

    assessment_means = []

    for column in assessment_columns:
        values = pd.to_numeric(
            learners[column],
            errors="coerce"
        )

        mean_value = values.mean()

        assessment_means.append(
            round(float(mean_value), 2)
            if pd.notna(mean_value)
            else None
        )

    # --------------------------------------------------------
    # Tracks and cohorts
    # --------------------------------------------------------

    tracks = sorted(
        learners["track_name"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    cohorts = sorted(
        learners["cohort_id"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    # --------------------------------------------------------
    # Employer skill frequencies
    # --------------------------------------------------------

    skill_counts = {}

    for skills in employers["required_skills"]:
        if not isinstance(skills, list):
            continue

        # Count a skill once per role, even if duplicated
        # within that role's skill list.
        unique_skills = {
            str(skill).strip()
            for skill in skills
            if str(skill).strip()
        }

        for skill in unique_skills:
            skill_counts[skill] = (
                skill_counts.get(skill, 0) + 1
            )

    sorted_skills = sorted(
        skill_counts.items(),
        key=lambda item: (-item[1], item[0].lower())
    )

    top_skills = [
        {
            "skill": skill,
            "count": count,
        }
        for skill, count in sorted_skills[:15]
    ]

    # --------------------------------------------------------
    # Employer role summary
    # --------------------------------------------------------

    employer_records = []

    for _, row in employers.iterrows():
        threshold = pd.to_numeric(
            pd.Series(
                [row.get("minimum_assessment_threshold")]
            ),
            errors="coerce"
        ).iloc[0]

        employer_records.append(
            {
                "role_id": str(row["role_id"]),
                "job_title": str(row["job_title"]),
                "company_tier": str(row["company_tier"]),
                "minimum_assessment_threshold": (
                    float(threshold)
                    if pd.notna(threshold)
                    else None
                ),
            }
        )

    # --------------------------------------------------------
    # Learner records
    # --------------------------------------------------------

    learner_columns = [
        "learner_id",
        "cohort_id",
        "track_name",
        "engagement_score",
        "average_module_score",
        "capstone_score",
        *module_columns,
    ]

    learner_records = []

    for _, row in learners.iterrows():
        record = {}

        for column in learner_columns:
            value = row[column]

            if pd.isna(value):
                record[column] = None
            elif column in [
                "engagement_score",
                "average_module_score",
                "capstone_score",
                *module_columns,
            ]:
                record[column] = float(value)
            else:
                record[column] = str(value)

        learner_records.append(record)

    # --------------------------------------------------------
    # Dashboard data payload
    # --------------------------------------------------------

    dashboard_data = {
        "learners": learner_records,
        "tracks": tracks,
        "cohorts": cohorts,
        "assessment_labels": assessment_labels,
        "assessment_means": assessment_means,
        "top_skills": top_skills,
        "employer_roles": employer_records,
        "total_roles": int(len(employers)),
    }

    return dashboard_data


# ============================================================
# 4. HTML DASHBOARD
# ============================================================

def build_dashboard_html(data):
    """Build the complete interactive HTML dashboard."""

    # Replace any non-standard JSON values with valid JSON nulls.
    payload = json.dumps(
        data,
        ensure_ascii=False,
        allow_nan=False
    )

    html_template = r"""<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>Sprints Talent Analytics Dashboard</title>

    <script src="https://cdn.plot.ly/plotly-3.1.0.min.js"></script>

    <style>
        :root {
            --background: #f4f7fb;
            --surface: #ffffff;
            --primary: #176b87;
            --secondary: #2a9d8f;
            --text: #172b4d;
            --muted: #64748b;
            --border: #e2e8f0;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, Helvetica, sans-serif;
            background: var(--background);
            color: var(--text);
        }

        .header {
            padding: 32px 5%;
            color: white;
            background: linear-gradient(
                120deg,
                #153e5c,
                #176b87,
                #2a9d8f
            );
        }

        .header h1 {
            margin: 0 0 10px;
            font-size: 30px;
        }

        .header p {
            margin: 0;
            color: #e0f2fe;
            line-height: 1.6;
        }

        .container {
            width: 92%;
            max-width: 1500px;
            margin: 26px auto;
        }

        .section-title {
            margin: 28px 0 15px;
            font-size: 21px;
        }

        .filters {
            display: grid;
            grid-template-columns: repeat(2, minmax(200px, 1fr));
            gap: 18px;
            padding: 22px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
        }

        .filter-group label {
            display: block;
            margin-bottom: 9px;
            font-weight: bold;
            font-size: 14px;
        }

        select {
            width: 100%;
            padding: 12px;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            background: white;
            color: var(--text);
            font-size: 14px;
        }

        .button-row {
            margin-top: 15px;
        }

        button {
            padding: 10px 18px;
            border: none;
            border-radius: 8px;
            background: var(--primary);
            color: white;
            font-weight: bold;
            cursor: pointer;
        }

        button:hover {
            opacity: 0.9;
        }

        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 18px;
            margin-top: 20px;
        }

        .kpi-card {
            padding: 22px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            box-shadow: 0 3px 12px rgba(15, 23, 42, 0.04);
        }

        .kpi-label {
            color: var(--muted);
            font-size: 13px;
            font-weight: bold;
        }

        .kpi-value {
            margin-top: 12px;
            font-size: 30px;
            font-weight: bold;
            color: var(--primary);
        }

        .kpi-description {
            margin-top: 8px;
            color: var(--muted);
            font-size: 12px;
        }

        .chart-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .chart-card {
            min-width: 0;
            padding: 18px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            box-shadow: 0 3px 12px rgba(15, 23, 42, 0.04);
        }

        .chart-card h3 {
            margin: 4px 8px;
            font-size: 16px;
        }

        .chart {
            width: 100%;
            height: 390px;
        }

        .full-width {
            grid-column: 1 / -1;
        }

        .table-wrapper {
            overflow-x: auto;
            margin-top: 20px;
            padding: 18px;
            background: white;
            border: 1px solid var(--border);
            border-radius: 14px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }

        th, td {
            padding: 13px;
            border-bottom: 1px solid var(--border);
            font-size: 13px;
        }

        th {
            background: #f1f5f9;
            color: var(--text);
        }

        tr:hover td {
            background: #f8fafc;
        }

        .footer {
            padding: 30px 15px;
            text-align: center;
            color: var(--muted);
            font-size: 12px;
        }

        .status {
            margin-top: 12px;
            color: var(--muted);
            font-size: 13px;
        }

        @media (max-width: 900px) {
            .kpi-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .chart-grid {
                grid-template-columns: 1fr;
            }

            .full-width {
                grid-column: auto;
            }
        }

        @media (max-width: 550px) {
            .header h1 {
                font-size: 23px;
            }

            .filters {
                grid-template-columns: 1fr;
            }

            .kpi-grid {
                grid-template-columns: 1fr;
            }

            .kpi-value {
                font-size: 26px;
            }
        }
    </style>
</head>

<body>

    <header class="header">
        <h1>Sprints Talent Analytics</h1>

        <p>
            Learner Performance, Cohort Insights,
            and Employer Skills Intelligence
        </p>

        <p style="margin-top: 10px;">
            Interactive analytics dashboard
        </p>
    </header>

    <main class="container">

        <h2 class="section-title">Dashboard Filters</h2>

        <section class="filters">

            <div class="filter-group">
                <label for="trackFilter">
                    Training Track
                </label>

                <select id="trackFilter">
                    <option value="ALL">All Tracks</option>
                </select>
            </div>

            <div class="filter-group">
                <label for="cohortFilter">
                    Cohort
                </label>

                <select id="cohortFilter">
                    <option value="ALL">All Cohorts</option>
                </select>
            </div>

        </section>

        <div class="button-row">
            <button id="resetButton">
                Reset Filters
            </button>

            <span class="status" id="filterStatus"></span>
        </div>

        <h2 class="section-title">Key Performance Indicators</h2>

        <section class="kpi-grid">

            <div class="kpi-card">
                <div class="kpi-label">
                    Learners in Selection
                </div>

                <div class="kpi-value" id="learnerKpi">
                    --
                </div>

                <div class="kpi-description">
                    Learners matching the selected filters
                </div>
            </div>

            <div class="kpi-card">
                <div class="kpi-label">
                    Training Tracks
                </div>

                <div class="kpi-value" id="trackKpi">
                    --
                </div>

                <div class="kpi-description">
                    Distinct tracks in the selection
                </div>
            </div>

            <div class="kpi-card">
                <div class="kpi-label">
                    Average Capstone Score
                </div>

                <div class="kpi-value" id="capstoneKpi">
                    --
                </div>

                <div class="kpi-description">
                    Calculated from available scores
                </div>
            </div>

            <div class="kpi-card">
                <div class="kpi-label">
                    Employer Roles
                </div>

                <div class="kpi-value" id="rolesKpi">
                    --
                </div>

                <div class="kpi-description">
                    Roles in the employer requirements dataset
                </div>
            </div>

        </section>

        <h2 class="section-title">
            Learner Performance Analysis
        </h2>

        <section class="chart-grid">

            <div class="chart-card">
                <h3>Average Assessment Scores</h3>
                <div id="assessmentChart" class="chart"></div>
            </div>

            <div class="chart-card">
                <h3>Average Capstone Score by Track</h3>
                <div id="trackChart" class="chart"></div>
            </div>

            <div class="chart-card full-width">
                <h3>Engagement vs Capstone Performance</h3>
                <div id="engagementChart" class="chart"></div>
            </div>

        </section>

        <h2 class="section-title">
            Employer Skills Intelligence
        </h2>

        <section class="chart-grid">

            <div class="chart-card full-width">
                <h3>Top 15 Most Requested Employer Skills</h3>
                <div id="skillsChart" class="chart"></div>
            </div>

        </section>

        <h2 class="section-title">
            Learner Performance Details
        </h2>

        <section class="table-wrapper">

            <table>
                <thead>
                    <tr>
                        <th>Learner ID</th>
                        <th>Track</th>
                        <th>Cohort</th>
                        <th>Engagement Score</th>
                        <th>Average Module Score</th>
                        <th>Capstone Score</th>
                    </tr>
                </thead>

                <tbody id="learnerTableBody"></tbody>
            </table>

            <p class="status" id="tableStatus"></p>

        </section>

        <div class="footer">
            Sprints Advanced Data Analysis Capstone |
            Data-driven insights for learner development
        </div>

    </main>

    <script>
        const DATA = __DASHBOARD_DATA__;

        const COLORS = {
            primary: "#176b87",
            secondary: "#2a9d8f",
            accent: "#e9c46a",
            purple: "#6554c0",
            grid: "#e2e8f0",
            text: "#172b4d"
        };

        const PLOT_CONFIG = {
            responsive: true,
            displaylogo: false,
            modeBarButtonsToRemove: ["lasso2d", "select2d"]
        };

        const PLOT_LAYOUT = {
            autosize: true,
            paper_bgcolor: "#ffffff",
            plot_bgcolor: "#ffffff",
            font: {
                family: "Arial, Helvetica, sans-serif",
                color: COLORS.text
            },
            margin: {
                l: 55,
                r: 25,
                t: 25,
                b: 65
            },
            xaxis: {
                gridcolor: COLORS.grid,
                automargin: true
            },
            yaxis: {
                gridcolor: COLORS.grid,
                automargin: true
            },
            showlegend: false
        };

        // ----------------------------------------------------
        // 1. Initialize dropdowns
        // ----------------------------------------------------

        function populateDropdown(id, values) {
            const dropdown = document.getElementById(id);

            values.forEach(value => {
                const option = document.createElement("option");

                option.value = value;
                option.textContent = value;

                dropdown.appendChild(option);
            });
        }

        populateDropdown("trackFilter", DATA.tracks);
        populateDropdown("cohortFilter", DATA.cohorts);


        // ----------------------------------------------------
        // 2. Utility functions
        // ----------------------------------------------------

        function average(values) {
            const valid = values.filter(
                value =>
                    value !== null &&
                    value !== undefined &&
                    Number.isFinite(Number(value))
            );

            if (valid.length === 0) {
                return null;
            }

            const total = valid.reduce(
                (sum, value) => sum + Number(value),
                0
            );

            return total / valid.length;
        }


        function formatScore(value) {
            if (value === null || value === undefined) {
                return "N/A";
            }

            if (!Number.isFinite(Number(value))) {
                return "N/A";
            }

            return Number(value).toFixed(2);
        }


        function formatNumber(value) {
            return Number(value).toLocaleString("en-US");
        }


        function getFilteredLearners() {
            const selectedTrack =
                document.getElementById("trackFilter").value;

            const selectedCohort =
                document.getElementById("cohortFilter").value;

            return DATA.learners.filter(learner => {
                const trackMatches =
                    selectedTrack === "ALL" ||
                    learner.track_name === selectedTrack;

                const cohortMatches =
                    selectedCohort === "ALL" ||
                    learner.cohort_id === selectedCohort;

                return trackMatches && cohortMatches;
            });
        }


        function cloneLayout(extra = {}) {
            return {
                ...PLOT_LAYOUT,
                ...extra
            };
        }


        // ----------------------------------------------------
        // 3. KPI cards
        // ----------------------------------------------------

        function updateKPIs(learners) {
            const distinctTracks = new Set(
                learners
                    .map(learner => learner.track_name)
                    .filter(Boolean)
            );

            const capstoneAverage = average(
                learners.map(learner => learner.capstone_score)
            );

            document.getElementById("learnerKpi").textContent =
                formatNumber(learners.length);

            document.getElementById("trackKpi").textContent =
                formatNumber(distinctTracks.size);

            document.getElementById("capstoneKpi").textContent =
                formatScore(capstoneAverage);

            document.getElementById("rolesKpi").textContent =
                formatNumber(DATA.total_roles);

            const trackValue =
                document.getElementById("trackFilter").value;

            const cohortValue =
                document.getElementById("cohortFilter").value;

            document.getElementById("filterStatus").textContent =
                "Showing " + learners.length + " learner(s)" +
                " | Track: " + trackValue +
                " | Cohort: " + cohortValue;
        }


        // ----------------------------------------------------
        // 4. Assessment chart
        // ----------------------------------------------------

        function updateAssessmentChart(learners) {
            // Recalculate every assessment mean from the currently
            // filtered learners. Missing scores are excluded.
            const moduleColumns = [
                "module_1_score", "module_2_score",
                "module_3_score", "module_4_score",
                "module_5_score", "module_6_score",
                "module_7_score", "module_8_score",
                "module_9_score", "module_10_score",
                "capstone_score"
            ];

            const labels = [
                "Module 1", "Module 2", "Module 3",
                "Module 4", "Module 5", "Module 6",
                "Module 7", "Module 8", "Module 9",
                "Module 10", "Capstone"
            ];

            const means = moduleColumns.map(column =>
                average(learners.map(learner => learner[column]))
            );

            const counts = moduleColumns.map(column =>
                learners.filter(learner =>
                    learner[column] !== null &&
                    learner[column] !== undefined &&
                    Number.isFinite(Number(learner[column]))
                ).length
            );

            Plotly.react(
                "assessmentChart",
                [{
                    type: "bar",
                    x: labels,
                    y: means,
                    customdata: counts,
                    marker: {
                        color: labels.map((label, index) =>
                            index === 10 ? COLORS.accent : COLORS.primary
                        )
                    },
                    text: means.map(value =>
                        value === null ? "" : formatScore(value)
                    ),
                    textposition: "outside",
                    hovertemplate:
                        "%{x}<br>Average score: %{y:.2f}" +
                        "<br>Valid scores: %{customdata}<extra></extra>"
                }],
                cloneLayout({
                    margin: {l: 55, r: 25, t: 35, b: 75},
                    xaxis: {
                        gridcolor: COLORS.grid,
                        automargin: true,
                        tickangle: -35
                    },
                    yaxis: {
                        title: "Average Score",
                        range: [0, 110],
                        gridcolor: COLORS.grid
                    }
                }),
                PLOT_CONFIG
            );
        }


        // ----------------------------------------------------
        // 5. Track comparison chart
        // ----------------------------------------------------

        function updateTrackChart(learners) {
            const grouped = {};

            learners.forEach(learner => {
                const track = learner.track_name || "Unknown";

                if (!grouped[track]) {
                    grouped[track] = [];
                }

                grouped[track].push(learner.capstone_score);
            });

            const tracks = Object.keys(grouped).sort();

            const scores = tracks.map(track =>
                average(grouped[track])
            );

            Plotly.react(
                "trackChart",
                [{
                    type: "bar",
                    x: tracks,
                    y: scores,
                    marker: {
                        color: COLORS.secondary
                    },
                    text: scores.map(formatScore),
                    textposition: "outside",
                    hovertemplate:
                        "Track: %{x}<br>" +
                        "Average capstone: %{y:.2f}<extra></extra>"
                }],
                cloneLayout({
                    margin: {
                        l: 50,
                        r: 20,
                        t: 25,
                        b: 115
                    },
                    xaxis: {
                        gridcolor: COLORS.grid,
                        tickangle: -25,
                        automargin: true
                    },
                    yaxis: {
                        title: "Average Capstone Score",
                        range: [0, 110],
                        gridcolor: COLORS.grid
                    }
                }),
                PLOT_CONFIG
            );
        }


        // ----------------------------------------------------
        // 6. Engagement vs capstone scatter chart
        // ----------------------------------------------------

        function updateEngagementChart(learners) {
            const validLearners = learners.filter(learner =>
                learner.engagement_score !== null &&
                learner.capstone_score !== null
            );

            const trace = {
                type: "scatter",
                mode: "markers",
                x: validLearners.map(
                    learner => learner.engagement_score
                ),
                y: validLearners.map(
                    learner => learner.capstone_score
                ),
                text: validLearners.map(
                    learner => learner.learner_id
                ),
                marker: {
                    size: 11,
                    color: COLORS.purple,
                    opacity: 0.8,
                    line: {
                        color: "#ffffff",
                        width: 1
                    }
                },
                hovertemplate:
                    "Learner: %{text}<br>" +
                    "Engagement: %{x:.2f}<br>" +
                    "Capstone: %{y:.2f}<extra></extra>"
            };

            Plotly.react(
                "engagementChart",
                [trace],
                cloneLayout({
                    margin: {
                        l: 65,
                        r: 25,
                        t: 25,
                        b: 60
                    },
                    xaxis: {
                        title: "Engagement Score",
                        gridcolor: COLORS.grid
                    },
                    yaxis: {
                        title: "Capstone Score",
                        gridcolor: COLORS.grid
                    }
                }),
                PLOT_CONFIG
            );
        }


        // ----------------------------------------------------
        // 7. Employer skills chart
        // ----------------------------------------------------

        function updateSkillsChart() {
            const skills = DATA.top_skills;

            const labels = skills
                .map(item => item.skill)
                .reverse();

            const counts = skills
                .map(item => item.count)
                .reverse();

            Plotly.react(
                "skillsChart",
                [{
                    type: "bar",
                    orientation: "h",
                    y: labels,
                    x: counts,
                    marker: {
                        color: labels.map(skill =>
                            skill.toLowerCase() === "python"
                                ? COLORS.accent
                                : COLORS.primary
                        )
                    },
                    text: counts,
                    textposition: "outside",
                    hovertemplate:
                        "Skill: %{y}<br>" +
                        "Roles requiring skill: %{x}<extra></extra>"
                }],
                cloneLayout({
                    margin: {
                        l: 145,
                        r: 55,
                        t: 20,
                        b: 50
                    },
                    xaxis: {
                        title: "Number of Roles",
                        rangemode: "tozero",
                        gridcolor: COLORS.grid
                    },
                    yaxis: {
                        title: "Skill",
                        automargin: true
                    }
                }),
                PLOT_CONFIG
            );
        }


        // ----------------------------------------------------
        // 8. Learner details table
        // ----------------------------------------------------

        function updateLearnerTable(learners) {
            const tableBody =
                document.getElementById("learnerTableBody");

            tableBody.replaceChildren();

            learners.forEach(learner => {
                const row = document.createElement("tr");

                const values = [
                    learner.learner_id,
                    learner.track_name,
                    learner.cohort_id,
                    formatScore(learner.engagement_score),
                    formatScore(learner.average_module_score),
                    formatScore(learner.capstone_score)
                ];

                values.forEach(value => {
                    const cell = document.createElement("td");

                    cell.textContent = value ?? "N/A";

                    row.appendChild(cell);
                });

                tableBody.appendChild(row);
            });

            document.getElementById("tableStatus").textContent =
                "Displaying " + learners.length + " learner record(s).";
        }


        // ----------------------------------------------------
        // 9. Refresh dashboard
        // ----------------------------------------------------

        function updateDashboard() {
            const learners = getFilteredLearners();

            updateKPIs(learners);
            updateAssessmentChart(learners);
            updateTrackChart(learners);
            updateEngagementChart(learners);
            updateLearnerTable(learners);
        }


        // ----------------------------------------------------
        // 10. Event listeners
        // ----------------------------------------------------

        document
            .getElementById("trackFilter")
            .addEventListener("change", updateDashboard);

        document
            .getElementById("cohortFilter")
            .addEventListener("change", updateDashboard);

        document
            .getElementById("resetButton")
            .addEventListener("click", function() {
                document.getElementById("trackFilter").value = "ALL";
                document.getElementById("cohortFilter").value = "ALL";

                updateDashboard();
            });


        // ----------------------------------------------------
        // 11. Initial render
        // ----------------------------------------------------

        updateSkillsChart();
        updateDashboard();
    </script>

</body>
</html>
"""

    return html_template.replace(
        "__DASHBOARD_DATA__",
        payload
    )


# ============================================================
# 5. MAIN
# ============================================================

def main():
    print("=" * 65)
    print("SPRINTS TALENT ANALYTICS - DASHBOARD GENERATOR")
    print("=" * 65)

    try:
        print("\n[1/4] Loading learner dataset...")

        learners = load_learner_data()

        print(f"      Learner records: {len(learners)}")
        print(f"      Learner columns: {len(learners.columns)}")

        print("\n[2/4] Loading employer requirements...")

        employers = load_employer_data()

        print(f"      Employer roles: {len(employers)}")

        print("\n[3/4] Preparing dashboard data...")

        dashboard_data = prepare_dashboard_data(
            learners,
            employers
        )

        print(
            "      Training tracks: "
            f"{len(dashboard_data['tracks'])}"
        )

        print(
            "      Cohorts: "
            f"{len(dashboard_data['cohorts'])}"
        )

        print(
            "      Skills displayed: "
            f"{len(dashboard_data['top_skills'])}"
        )

        print("\n[4/4] Generating HTML dashboard...")

        html_content = build_dashboard_html(
            dashboard_data
        )

        OUTPUT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        OUTPUT_PATH.write_text(
            html_content,
            encoding="utf-8"
        )

        print("\n" + "=" * 65)
        print("DASHBOARD GENERATED SUCCESSFULLY")
        print("=" * 65)

        print(f"\nOutput file: {OUTPUT_PATH}")
        print(
            f"File size: {OUTPUT_PATH.stat().st_size:,} bytes"
        )

        print("\nDashboard components:")
        print("  - KPI cards")
        print("  - Track and cohort filters")
        print("  - Assessment performance chart")
        print("  - Capstone performance by track")
        print("  - Engagement vs capstone scatter plot")
        print("  - Employer skills chart")
        print("  - Learner details table")

        print("\nNext step:")
        print("  Open dashboard/index.html in your browser.")

        return 0

    except Exception as error:
        print("\nDASHBOARD GENERATION FAILED")
        print(f"Error: {error}")

        return 1


if __name__ == "__main__":
    sys.exit(main())