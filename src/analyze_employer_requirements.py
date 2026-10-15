import json
from collections import Counter
from pathlib import Path

import numpy as np


# ============================================================
# SPRINTS TALENT ANALYTICS
# Employer Requirements Analysis
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    ROOT_DIR
    / "data"
    / "employer_partner_requirements.json"
)

OUTPUT_PATH = (
    ROOT_DIR
    / "reports"
    / "employer_requirements_summary.json"
)


def load_requirements():
    """Load employer requirements and validate the JSON structure."""

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Employer requirements file not found: {INPUT_PATH}"
        )

    with open(INPUT_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            "Expected the top-level JSON structure to be an object."
        )

    requirements = data.get("employer_requirements")

    if not isinstance(requirements, list):
        raise ValueError(
            "Expected 'employer_requirements' to be a list."
        )

    if not requirements:
        raise ValueError(
            "The employer requirements list is empty."
        )

    invalid_records = [
        index
        for index, requirement in enumerate(requirements)
        if not isinstance(requirement, dict)
    ]

    if invalid_records:
        raise ValueError(
            f"Invalid requirement records at positions: {invalid_records}"
        )

    return data, requirements


def inspect_structure(requirements):
    """Inspect fields and identify missing values."""

    all_fields = sorted(
        {
            field
            for requirement in requirements
            for field in requirement.keys()
        }
    )

    missing_fields = {}

    for field in all_fields:
        missing_count = sum(
            1
            for requirement in requirements
            if field not in requirement
            or requirement[field] is None
            or (
                isinstance(requirement[field], str)
                and requirement[field].strip() == ""
            )
        )

        missing_fields[field] = missing_count

    return {
        "fields": all_fields,
        "missing_fields": missing_fields,
        "non_object_records": 0,
    }


def analyze_role_ids(requirements):
    """Check role ID completeness and duplicates."""

    role_ids = []
    missing_role_id_records = 0

    for requirement in requirements:
        role_id = requirement.get("role_id")

        if role_id is None or str(role_id).strip() == "":
            missing_role_id_records += 1
        else:
            role_ids.append(str(role_id).strip())

    counts = Counter(role_ids)

    duplicate_ids = {
        role_id: count
        for role_id, count in counts.items()
        if count > 1
    }

    return {
        "total_records": len(requirements),
        "records_with_role_id": len(role_ids),
        "missing_role_id_records": missing_role_id_records,
        "unique_role_ids": len(set(role_ids)),
        "duplicate_role_ids": duplicate_ids,
    }


def analyze_skills(requirements):
    """Analyze required skills without changing their original names."""

    skill_counter = Counter()
    roles_without_skills = 0
    malformed_skill_lists = 0

    for requirement in requirements:
        skills = requirement.get("required_skills")

        if not isinstance(skills, list):
            malformed_skill_lists += 1
            roles_without_skills += 1
            continue

        valid_skills = [
            str(skill).strip()
            for skill in skills
            if skill is not None and str(skill).strip()
        ]

        if not valid_skills:
            roles_without_skills += 1

        # Count each skill at most once per role.
        skill_counter.update(set(valid_skills))

    ordered_skills = sorted(
        skill_counter.items(),
        key=lambda item: (-item[1], item[0].lower()),
    )

    return {
        "unique_skill_count": len(skill_counter),
        "roles_without_skills": roles_without_skills,
        "malformed_skill_lists": malformed_skill_lists,
        "skill_frequency": dict(ordered_skills),
    }


def analyze_numeric_fields(requirements):
    """Summarize the actual numeric fields in the source JSON."""

    numeric_fields = {}

    # These names match the actual JSON structure.
    candidate_fields = [
        "priority_weight",
        "minimum_assessment_threshold",
    ]

    for field in candidate_fields:
        values = []
        invalid_values = 0

        for requirement in requirements:
            value = requirement.get(field)

            if value is None or isinstance(value, bool):
                invalid_values += 1
                continue

            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                invalid_values += 1
                continue

            if not np.isfinite(numeric_value):
                invalid_values += 1
                continue

            values.append(numeric_value)

        if values:
            numeric_fields[field] = {
                "valid_count": len(values),
                "invalid_or_missing_count": invalid_values,
                "minimum": round(float(np.min(values)), 3),
                "maximum": round(float(np.max(values)), 3),
                "mean": round(float(np.mean(values)), 3),
                "median": round(float(np.median(values)), 3),
            }
        else:
            numeric_fields[field] = {
                "valid_count": 0,
                "invalid_or_missing_count": invalid_values,
                "minimum": None,
                "maximum": None,
                "mean": None,
                "median": None,
            }

    return numeric_fields


def summarize_categories(requirements, field):
    """Count values for a categorical field."""

    counter = Counter()

    for requirement in requirements:
        value = requirement.get(field)

        if value is None or (
            isinstance(value, str)
            and value.strip() == ""
        ):
            counter["Missing"] += 1
        else:
            counter[str(value).strip()] += 1

    return dict(
        sorted(
            counter.items(),
            key=lambda item: (-item[1], item[0].lower()),
        )
    )


def main():
    print("=" * 70)
    print("SPRINTS TALENT ANALYTICS")
    print("EMPLOYER REQUIREMENTS ANALYSIS")
    print("=" * 70)

    source_data, requirements = load_requirements()

    print("\n1. SOURCE OVERVIEW")
    print("-" * 70)

    print(f"Requirement records: {len(requirements)}")
    print(f"Top-level JSON keys: {list(source_data.keys())}")

    # --------------------------------------------------------
    # 2. Structure and role ID validation
    # --------------------------------------------------------

    structure_summary = inspect_structure(requirements)
    role_id_summary = analyze_role_ids(requirements)

    print("\n2. JSON STRUCTURE")
    print("-" * 70)

    print("Fields:")

    for field in structure_summary["fields"]:
        print(f"- {field}")

    print(
        "\nRecords that are not JSON objects:",
        structure_summary["non_object_records"],
    )

    print("\nMissing values by field:")

    for field, count in structure_summary["missing_fields"].items():
        print(f"{field}: {count}")

    print("\nRole ID validation:")
    print(json.dumps(role_id_summary, indent=2))

    # --------------------------------------------------------
    # 3. Required skills
    # --------------------------------------------------------

    skill_summary = analyze_skills(requirements)

    print("\n3. REQUIRED SKILLS")
    print("-" * 70)

    print("Unique skills:", skill_summary["unique_skill_count"])
    print("Roles without skills:", skill_summary["roles_without_skills"])
    print(
        "Malformed skill lists:",
        skill_summary["malformed_skill_lists"],
    )

    print("\nMost frequently required skills:")

    for skill, count in list(
        skill_summary["skill_frequency"].items()
    )[:20]:
        print(f"{skill}: {count} roles")

    # --------------------------------------------------------
    # 4. Role distributions
    # --------------------------------------------------------

    category_fields = {
        "job_title": "Job title",
        "company_tier": "Company tier",
        "industry": "Industry",
    }

    category_summaries = {}

    print("\n4. ROLE DISTRIBUTION")
    print("-" * 70)

    for field, label in category_fields.items():
        summary = summarize_categories(requirements, field)
        category_summaries[field] = summary

        print(f"\n{label}:")

        for category, count in summary.items():
            print(f"  {category}: {count}")

    # --------------------------------------------------------
    # 5. Numeric fields
    # --------------------------------------------------------

    numeric_summary = analyze_numeric_fields(requirements)

    print("\n5. NUMERIC FIELD SUMMARY")
    print("-" * 70)

    print(json.dumps(numeric_summary, indent=2))

    # --------------------------------------------------------
    # 6. Basic consistency checks
    # --------------------------------------------------------

    consistency_checks = {
        "all_records_have_role_id": (
            role_id_summary["missing_role_id_records"] == 0
        ),
        "all_role_ids_are_unique": (
            role_id_summary["unique_role_ids"] == len(requirements)
            and not role_id_summary["duplicate_role_ids"]
        ),
        "all_records_have_required_skills": (
            skill_summary["roles_without_skills"] == 0
        ),
        "all_records_have_job_title": (
            category_summaries["job_title"].get("Missing", 0) == 0
        ),
        "all_records_have_company_tier": (
            category_summaries["company_tier"].get("Missing", 0) == 0
        ),
    }

    print("\n6. CONSISTENCY CHECKS")
    print("-" * 70)

    for check, passed in consistency_checks.items():
        status = "PASS" if passed else "REVIEW"
        print(f"{status}: {check}")

    # --------------------------------------------------------
    # 7. Save report
    # --------------------------------------------------------

    report = {
        "source_file": str(INPUT_PATH.relative_to(ROOT_DIR)),
        "total_requirement_records": len(requirements),
        "structure": structure_summary,
        "role_id_validation": role_id_summary,
        "skills": skill_summary,
        "category_summaries": category_summaries,
        "numeric_summary": numeric_summary,
        "consistency_checks": consistency_checks,
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
    print("EMPLOYER REQUIREMENTS ANALYSIS COMPLETED")
    print("=" * 70)
    print(f"Report saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()