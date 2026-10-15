import json
from pathlib import Path

import pandas as pd
import plotly.express as px


# ============================================================
# SPRINTS TALENT ANALYTICS
# Interactive Data Visualization
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

LEARNERS_PATH = (
    ROOT_DIR / "data" / "sprints_cohort_features.csv"
)

EMPLOYERS_PATH = (
    ROOT_DIR
    / "data"
    / "employer_partner_requirements.json"
)

OUTPUT_DIR = ROOT_DIR / "reports" / "figures"


def load_data():
    """Load learner features and employer requirements."""

    if not LEARNERS_PATH.exists():
        raise FileNotFoundError(
            f"Learner feature dataset not found: {LEARNERS_PATH}"
        )

    if not EMPLOYERS_PATH.exists():
        raise FileNotFoundError(
            f"Employer requirements not found: {EMPLOYERS_PATH}"
        )

    learners = pd.read_csv(LEARNERS_PATH)

    learners["enrollment_date"] = pd.to_datetime(
        learners["enrollment_date"],
        errors="coerce",
    )

    learners["graduation_date"] = pd.to_datetime(
        learners["graduation_date"],
        errors="coerce",
    )

    with open(EMPLOYERS_PATH, "r", encoding="utf-8") as file:
        employer_data = json.load(file)

    requirements = employer_data.get("employer_requirements")

    if not isinstance(requirements, list):
        raise ValueError(
            "Invalid employer requirements JSON structure."
        )

    employers = pd.DataFrame(requirements)

    return learners, employers


def save_figure(fig, filename):
    """Save a Plotly figure as a standalone HTML file."""

    output_path = OUTPUT_DIR / filename

    fig.write_html(
        str(output_path),
        include_plotlyjs=True,
        full_html=True,
    )

    print(f"Saved: {output_path}")


def create_track_chart(learners):
    """Create a learner distribution chart by track."""

    counts = (
        learners["track_name"]
        .fillna("Missing")
        .value_counts()
        .rename_axis("Track")
        .reset_index(name="Learner Count")
    )

    fig = px.bar(
        counts,
        x="Track",
        y="Learner Count",
        color="Track",
        title="Learner Distribution by Training Track",
        text="Learner Count",
        template="plotly_white",
    )

    fig.update_layout(
        xaxis_title="Training Track",
        yaxis_title="Number of Learners",
        showlegend=False,
    )

    fig.update_traces(
        textposition="outside",
    )

    save_figure(fig, "01_track_distribution.html")


def create_cohort_chart(learners):
    """Create a learner distribution chart by cohort."""

    counts = (
        learners["cohort_id"]
        .fillna("Missing")
        .value_counts()
        .rename_axis("Cohort")
        .reset_index(name="Learner Count")
        .sort_values("Cohort")
    )

    fig = px.bar(
        counts,
        x="Cohort",
        y="Learner Count",
        color="Learner Count",
        title="Learner Distribution by Cohort",
        text="Learner Count",
        color_continuous_scale="Blues",
        template="plotly_white",
    )

    fig.update_layout(
        xaxis_title="Cohort",
        yaxis_title="Number of Learners",
        coloraxis_showscale=False,
    )

    fig.update_traces(
        textposition="outside",
    )

    save_figure(fig, "02_cohort_distribution.html")


def create_module_chart(learners):
    """Compare mean scores across modules and capstone."""

    module_columns = [
        f"module_{number}_score"
        for number in range(1, 11)
    ]

    score_columns = module_columns + ["capstone_score"]

    score_data = []

    for column in score_columns:
        values = pd.to_numeric(
            learners[column],
            errors="coerce",
        ).dropna()

        score_data.append(
            {
                "Assessment": (
                    column.replace("_score", "")
                    .replace("_", " ")
                    .title()
                ),
                "Mean Score": (
                    round(float(values.mean()), 2)
                    if not values.empty
                    else None
                ),
                "Valid Learners": int(values.count()),
            }
        )

    summary = pd.DataFrame(score_data)

    fig = px.bar(
        summary,
        x="Assessment",
        y="Mean Score",
        color="Mean Score",
        hover_data=["Valid Learners"],
        title="Average Assessment Scores",
        text="Mean Score",
        color_continuous_scale="Tealgrn",
        template="plotly_white",
    )

    fig.update_layout(
        xaxis_title="Assessment",
        yaxis_title="Average Score",
        yaxis_range=[0, 105],
        coloraxis_showscale=False,
    )

    fig.update_traces(
        textposition="outside",
        texttemplate="%{text:.2f}",
    )

    save_figure(fig, "03_assessment_scores.html")


def create_average_score_distribution(learners):
    """Show the distribution of learner average module scores."""

    data = learners.loc[
        learners["average_module_score"].notna(),
        ["learner_id", "average_module_score"],
    ].copy()

    fig = px.histogram(
        data,
        x="average_module_score",
        nbins=8,
        title="Distribution of Average Module Scores",
        labels={
            "average_module_score": "Average Module Score",
            "count": "Number of Learners",
        },
        template="plotly_white",
        hover_data=["learner_id"],
    )

    fig.update_layout(
        xaxis_title="Average Module Score",
        yaxis_title="Number of Learners",
        bargap=0.08,
    )

    save_figure(fig, "04_average_score_distribution.html")


def create_engagement_capstone_chart(learners):
    """Explore the relationship between engagement and capstone."""

    data = learners[
        [
            "learner_id",
            "engagement_score",
            "capstone_score",
            "track_name",
        ]
    ].dropna(
        subset=[
            "engagement_score",
            "capstone_score",
        ]
    ).copy()

    fig = px.scatter(
        data,
        x="engagement_score",
        y="capstone_score",
        color="track_name",
        hover_data=["learner_id"],
        title="Engagement Score vs. Capstone Score",
        labels={
            "engagement_score": "Engagement Score",
            "capstone_score": "Capstone Score",
            "track_name": "Training Track",
        },
        template="plotly_white",
    )

    fig.update_layout(
        xaxis_title="Engagement Score",
        yaxis_title="Capstone Score",
    )

    save_figure(fig, "05_engagement_vs_capstone.html")


def create_module_completeness_chart(learners):
    """Explore average scores against available module counts."""

    data = learners[
        [
            "learner_id",
            "module_score_count",
            "average_module_score",
            "track_name",
        ]
    ].dropna(
        subset=[
            "module_score_count",
            "average_module_score",
        ]
    ).copy()

    data["module_score_count"] = (
        data["module_score_count"].astype(int)
    )

    fig = px.scatter(
        data,
        x="module_score_count",
        y="average_module_score",
        color="track_name",
        hover_data=["learner_id"],
        title="Average Score vs. Available Module Scores",
        labels={
            "module_score_count": "Number of Available Module Scores",
            "average_module_score": "Average Module Score",
            "track_name": "Training Track",
        },
        template="plotly_white",
    )

    fig.update_layout(
        xaxis_title="Number of Available Module Scores",
        yaxis_title="Average Module Score",
        xaxis=dict(dtick=1),
    )

    save_figure(fig, "06_score_vs_module_completeness.html")


def create_company_tier_chart(employers):
    """Show the number of roles in each company tier."""

    if "company_tier" not in employers.columns:
        raise ValueError(
            "The company_tier field is missing from employer data."
        )

    counts = (
        employers["company_tier"]
        .fillna("Missing")
        .value_counts()
        .rename_axis("Company Tier")
        .reset_index(name="Role Count")
    )

    fig = px.bar(
        counts,
        x="Company Tier",
        y="Role Count",
        color="Company Tier",
        title="Employer Roles by Company Tier",
        text="Role Count",
        template="plotly_white",
    )

    fig.update_layout(
        xaxis_title="Company Tier",
        yaxis_title="Number of Roles",
        showlegend=False,
    )

    fig.update_traces(
        textposition="outside",
    )

    save_figure(fig, "07_company_tier_distribution.html")


def create_skill_frequency_chart(employers):
    """Show the most frequently required employer skills."""

    skill_counter = {}

    for skills in employers["required_skills"]:
        if not isinstance(skills, list):
            continue

        # Each skill is counted once per role.
        for skill in set(
            str(skill).strip()
            for skill in skills
            if skill is not None and str(skill).strip()
        ):
            skill_counter[skill] = (
                skill_counter.get(skill, 0) + 1
            )

    if not skill_counter:
        raise ValueError(
            "No valid employer skills were found."
        )

    skill_data = pd.DataFrame(
        [
            {
                "Skill": skill,
                "Role Count": count,
            }
            for skill, count in skill_counter.items()
        ]
    )

    skill_data = skill_data.sort_values(
        ["Role Count", "Skill"],
        ascending=[True, True],
    ).tail(15)

    fig = px.bar(
        skill_data,
        x="Role Count",
        y="Skill",
        orientation="h",
        color="Role Count",
        title="Top 15 Most Requested Employer Skills",
        text="Role Count",
        color_continuous_scale="Viridis",
        template="plotly_white",
    )

    fig.update_layout(
        xaxis_title="Number of Roles Requiring the Skill",
        yaxis_title="Skill",
        coloraxis_showscale=False,
    )

    fig.update_traces(
        textposition="outside",
    )

    save_figure(fig, "08_top_employer_skills.html")


def main():
    print("=" * 70)
    print("SPRINTS TALENT ANALYTICS")
    print("INTERACTIVE DATA VISUALIZATION")
    print("=" * 70)

    learners, employers = load_data()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(f"\nLearner records: {len(learners)}")
    print(f"Employer roles: {len(employers)}")
    print(f"Output directory: {OUTPUT_DIR}")

    charts = [
        ("Track distribution", create_track_chart),
        ("Cohort distribution", create_cohort_chart),
        ("Assessment scores", create_module_chart),
        (
            "Average score distribution",
            create_average_score_distribution,
        ),
        (
            "Engagement vs. capstone",
            create_engagement_capstone_chart,
        ),
        (
            "Score vs. module completeness",
            create_module_completeness_chart,
        ),
        ("Company tier distribution", create_company_tier_chart),
        ("Employer skill frequency", create_skill_frequency_chart),
    ]

    successful_charts = 0
    failed_charts = []

    for chart_name, chart_function in charts:
        print(f"\nGenerating: {chart_name}")

        try:
            chart_function(
                learners
                if chart_function
                in [
                    create_track_chart,
                    create_cohort_chart,
                    create_module_chart,
                    create_average_score_distribution,
                    create_engagement_capstone_chart,
                    create_module_completeness_chart,
                ]
                else employers
            )

            successful_charts += 1

        except Exception as error:
            failed_charts.append(
                {
                    "chart": chart_name,
                    "error": str(error),
                }
            )

            print(f"ERROR: {error}")

    print("\n" + "=" * 70)
    print("VISUALIZATION SUMMARY")
    print("=" * 70)

    print(f"Successful charts: {successful_charts}")
    print(f"Failed charts: {len(failed_charts)}")

    if failed_charts:
        print("\nFailed charts:")

        for failure in failed_charts:
            print(f"- {failure['chart']}: {failure['error']}")

    print(f"\nFigures directory: {OUTPUT_DIR}")

    if failed_charts:
        raise RuntimeError(
            "Some charts failed. Review the errors above."
        )

    print("\nAll charts generated successfully.")


if __name__ == "__main__":
    main()