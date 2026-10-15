import json
from pathlib import Path

import pandas as pd


# ============================================================
# SPRINTS TALENT ANALYTICS
# Feature Engineering Readiness Check
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

LEARNERS_PATH = ROOT_DIR / "data" / "sprints_cohort_clean.csv"

EMPLOYERS_PATH = (
    ROOT_DIR
    / "data"
    / "employer_partner_requirements.json"
)

OUTPUT_PATH = (
    ROOT_DIR
    / "reports"
    / "feature_engineering_readiness.json"
)


def load_inputs():
    """Load cleaned learner data and employer requirements."""

    if not LEARNERS_PATH.exists():
        raise FileNotFoundError(
            f"Learner dataset not found: {LEARNERS_PATH}"
        )

    if not EMPLOYERS_PATH.exists():
        raise FileNotFoundError(
            f"Employer requirements not found: {EMPLOYERS_PATH}"
        )

    learners = pd.read_csv(LEARNERS_PATH)

    with open(EMPLOYERS_PATH, "r", encoding="utf-8") as file:
        employer_data = json.load(file)

    requirements = employer_data.get("employer_requirements")

    if not isinstance(requirements, list):
        raise ValueError(
            "Expected 'employer_requirements' to be a list."
        )

    return learners, requirements


def inspect_learner_features(learners):
    """Identify existing and potentially derivable learner features."""

    module_columns = sorted(
        [
            column
            for column in learners.columns
            if column.startswith("module_")
            and column.endswith("_score")
        ],
        key=lambda column: int(
            column.removeprefix("module_").removesuffix("_score")
        ),
    )

    score_columns = [
        column
        for column in learners.columns
        if column.endswith("_score")
    ]

    existing_features = {
        "learner_identifiers": [
            column
            for column in ["learner_id", "cohort_id"]
            if column in learners.columns
        ],
        "categorical_features": [
            column
            for column in [
                "demographic_group",
                "track_name",
            ]
            if column in learners.columns
        ],
        "date_features": [
            column
            for column in [
                "enrollment_date",
                "graduation_date",
            ]
            if column in learners.columns
        ],
        "score_features": score_columns,
        "module_features": module_columns,
    }

    potential_features = [
        {
            "feature": "average_module_score",
            "description": (
                "Mean of available module scores for each learner."
            ),
            "requires_validation": (
                "Confirm that module scores share the same scale."
            ),
        },
        {
            "feature": "module_score_count",
            "description": (
                "Number of non-missing module scores for each learner."
            ),
            "requires_validation": (
                "Interpret missing scores as unavailable, not zero."
            ),
        },
        {
            "feature": "module_score_std",
            "description": (
                "Standard deviation of available module scores "
                "for each learner."
            ),
            "requires_validation": (
                "Calculate only when enough module scores are present."
            ),
        },
        {
            "feature": "enrollment_year",
            "description": (
                "Year extracted from enrollment_date."
            ),
            "requires_validation": (
                "Confirm date parsing before deriving the feature."
            ),
        },
        {
            "feature": "days_to_graduation",
            "description": (
                "Difference between graduation_date and enrollment_date."
            ),
            "requires_validation": (
                "Only calculate when both dates are available."
            ),
        },
    ]

    return {
        "existing_features": existing_features,
        "potential_features": potential_features,
        "module_score_missing_counts": {
            column: int(learners[column].isna().sum())
            for column in module_columns
        },
        "module_score_valid_counts": {
            column: int(learners[column].notna().sum())
            for column in module_columns
        },
    }


def inspect_skill_requirements(requirements):
    """Summarize employer skill names and thresholds."""

    skill_roles = {}
    threshold_values = []
    priority_values = []

    for role in requirements:
        role_id = role.get("role_id")
        job_title = role.get("job_title")
        tier = role.get("company_tier")

        threshold = role.get("minimum_assessment_threshold")
        priority = role.get("priority_weight")

        if threshold is not None:
            try:
                threshold_values.append(float(threshold))
            except (TypeError, ValueError):
                pass

        if priority is not None:
            try:
                priority_values.append(float(priority))
            except (TypeError, ValueError):
                pass

        skills = role.get("required_skills", [])

        if not isinstance(skills, list):
            continue

        for skill in skills:
            if skill is None or not str(skill).strip():
                continue

            skill_name = str(skill).strip()

            skill_roles.setdefault(
                skill_name,
                [],
            ).append(
                {
                    "role_id": role_id,
                    "job_title": job_title,
                    "company_tier": tier,
                    "minimum_assessment_threshold": threshold,
                    "priority_weight": priority,
                }
            )

    skill_frequency = {
        skill: len(roles)
        for skill, roles in sorted(
            skill_roles.items(),
            key=lambda item: (
                -len(item[1]),
                item[0].lower(),
            ),
        )
    }

    return {
        "unique_skills": len(skill_roles),
        "skill_frequency": skill_frequency,
        "threshold_count": len(threshold_values),
        "threshold_minimum": (
            min(threshold_values)
            if threshold_values
            else None
        ),
        "threshold_maximum": (
            max(threshold_values)
            if threshold_values
            else None
        ),
        "priority_count": len(priority_values),
        "priority_minimum": (
            min(priority_values)
            if priority_values
            else None
        ),
        "priority_maximum": (
            max(priority_values)
            if priority_values
            else None
        ),
    }


def main():
    print("=" * 70)
    print("SPRINTS TALENT ANALYTICS")
    print("FEATURE ENGINEERING READINESS CHECK")
    print("=" * 70)

    learners, requirements = load_inputs()

    learner_summary = inspect_learner_features(learners)

    employer_summary = inspect_skill_requirements(requirements)

    print("\n1. LEARNER DATA")
    print("-" * 70)

    print(f"Learners: {len(learners)}")
    print(f"Columns: {len(learners.columns)}")

    print("\nModule score columns:")

    for column in learner_summary["existing_features"]["module_features"]:
        print(
            f"{column}: "
            f"{learner_summary['module_score_valid_counts'][column]} "
            f"valid, "
            f"{learner_summary['module_score_missing_counts'][column]} "
            f"missing"
        )

    print("\nPotential features:")

    for feature in learner_summary["potential_features"]:
        print(f"\n{feature['feature']}")
        print(f"Description: {feature['description']}")
        print(
            "Validation: "
            f"{feature['requires_validation']}"
        )

    print("\n2. EMPLOYER SKILL REQUIREMENTS")
    print("-" * 70)

    print(f"Roles: {len(requirements)}")
    print(f"Unique skills: {employer_summary['unique_skills']}")

    print("\nMost requested skills:")

    for skill, count in list(
        employer_summary["skill_frequency"].items()
    )[:15]:
        print(f"{skill}: {count} roles")

    print("\nThreshold range:")
    print(
        f"{employer_summary['threshold_minimum']} "
        f"to {employer_summary['threshold_maximum']}"
    )

    print("\nPriority weight range:")
    print(
        f"{employer_summary['priority_minimum']} "
        f"to {employer_summary['priority_maximum']}"
    )

    report = {
        "learner_data": {
            "record_count": int(len(learners)),
            "column_count": int(len(learners.columns)),
            **learner_summary,
        },
        "employer_requirements": {
            "role_count": len(requirements),
            **employer_summary,
        },
        "skill_mapping_status": (
            "Not established: learner module scores do not "
            "directly identify individual skills."
        ),
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )

    print("\n" + "=" * 70)
    print("READINESS CHECK COMPLETED")
    print("=" * 70)
    print(f"Report saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()