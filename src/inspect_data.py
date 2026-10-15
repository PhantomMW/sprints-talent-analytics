from pathlib import Path
import csv
import json

import pandas as pd


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

CSV_PATH = DATA_DIR / "sprints_cohort_data_2023.csv"
JSON_PATH = DATA_DIR / "employer_partner_requirements.json"


# ============================================================
# CSV LOADING
# ============================================================

def load_cohort_data(file_path: Path) -> pd.DataFrame:
    """
    Load cohort CSV data while repairing only extra trailing
    empty fields that exceed the header width.

    The original CSV file is never modified.
    """

    if not file_path.exists():
        raise FileNotFoundError(
            f"Cohort CSV file not found: {file_path}"
        )

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        rows = list(csv.reader(file))

    if not rows:
        raise ValueError("The cohort CSV file is empty.")

    header = rows[0]
    expected_columns = len(header)

    if len(header) != len(set(header)):
        raise ValueError(
            "The CSV header contains duplicate column names."
        )

    repaired_rows = []
    repaired_records = []

    for line_number, original_row in enumerate(
        rows[1:],
        start=2
    ):
        row = original_row.copy()
        original_field_count = len(row)

        # Remove extra trailing empty fields only.
        while len(row) > expected_columns and row[-1] == "":
            row.pop()

        # Do not silently repair any other structural issue.
        if len(row) != expected_columns:
            raise ValueError(
                f"CSV line {line_number} contains "
                f"{len(row)} fields; expected {expected_columns}."
            )

        if len(row) != original_field_count:
            repaired_records.append({
                "line_number": line_number,
                "learner_id": row[0] if row else None,
                "original_fields": original_field_count,
                "final_fields": len(row),
            })

        repaired_rows.append(row)

    df = pd.DataFrame(
        repaired_rows,
        columns=header
    )

    # Convert empty strings to missing values.
    df = df.replace(r"^\s*$", pd.NA, regex=True)

    print("\nCSV loading summary")
    print("-" * 60)
    print(f"Original file: {file_path.name}")
    print(f"Expected columns: {expected_columns}")
    print(f"Loaded records: {len(df)}")
    print(f"Rows requiring structural repair: {len(repaired_records)}")

    for record in repaired_records:
        print(record)

    return df


# ============================================================
# DATA QUALITY AUDIT
# ============================================================

def audit_data_quality(df: pd.DataFrame) -> None:
    """
    Inspect duplicate records, missing values, numeric scores,
    engagement scores, and date validity without modifying df.
    """

    print("\n" + "=" * 60)
    print("DATA QUALITY AUDIT")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Dataset overview
    # --------------------------------------------------------

    print("\n1. Dataset overview")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    # --------------------------------------------------------
    # 2. Duplicate full records
    # --------------------------------------------------------

    print("\n2. Fully duplicated records")

    duplicate_mask = df.duplicated(keep=False)
    duplicate_records = df.loc[duplicate_mask]

    print(
        "Rows belonging to duplicate groups:",
        int(duplicate_mask.sum())
    )
    print(
        "Extra duplicate rows:",
        int(df.duplicated().sum())
    )

    if not duplicate_records.empty:
        print(
            duplicate_records.to_string(index=False)
        )

    # --------------------------------------------------------
    # 3. Duplicate learner IDs
    # --------------------------------------------------------

    print("\n3. Duplicate learner IDs")

    if "learner_id" in df.columns:
        learner_id_mask = df["learner_id"].duplicated(
            keep=False
        )

        duplicate_ids = df.loc[
            learner_id_mask,
            [
                column
                for column in [
                    "learner_id",
                    "cohort_id",
                    "track_name"
                ]
                if column in df.columns
            ]
        ].sort_values("learner_id")

        print(
            "Rows with repeated learner IDs:",
            int(learner_id_mask.sum())
        )

        if duplicate_ids.empty:
            print("No repeated learner IDs found.")
        else:
            print(duplicate_ids.to_string(index=False))

    # --------------------------------------------------------
    # 4. Missing values
    # --------------------------------------------------------

    print("\n4. Missing values per column")

    missing_counts = df.isna().sum()

    print(missing_counts.to_string())

    print(
        "\nTotal missing cells:",
        int(missing_counts.sum())
    )

    # --------------------------------------------------------
    # 5. Data types
    # --------------------------------------------------------

    print("\n5. Original data types")

    print(df.dtypes.to_string())

    # --------------------------------------------------------
    # 6. Numeric score validation
    # --------------------------------------------------------

    print("\n6. Score values outside the expected 0-100 range")

    score_columns = [
        column
        for column in df.columns
        if column.endswith("_score")
    ]

    for column in score_columns:
        numeric_values = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        invalid_mask = (
            (numeric_values < 0)
            | (numeric_values > 100)
        )

        invalid_rows = df.loc[
            invalid_mask.fillna(False),
            ["learner_id", column]
        ]

        non_numeric_mask = (
            df[column].notna()
            & numeric_values.isna()
        )

        non_numeric_rows = df.loc[
            non_numeric_mask,
            ["learner_id", column]
        ]

        if not invalid_rows.empty:
            print(f"\n{column} — out-of-range values:")
            print(invalid_rows.to_string(index=False))

        if not non_numeric_rows.empty:
            print(f"\n{column} — non-numeric values:")
            print(non_numeric_rows.to_string(index=False))

        if invalid_rows.empty and non_numeric_rows.empty:
            print(f"{column}: no detected range/type issues.")

    # --------------------------------------------------------
    # 7. Engagement score summary
    # --------------------------------------------------------

    print("\n7. Engagement score summary")

    if "engagement_score" in df.columns:
        engagement = pd.to_numeric(
            df["engagement_score"],
            errors="coerce"
        )

        print(engagement.describe().to_string())

    # --------------------------------------------------------
    # 8. Date validation
    # --------------------------------------------------------

    print("\n8. Date parsing audit")

    date_columns = [
        column
        for column in [
            "enrollment_date",
            "graduation_date"
        ]
        if column in df.columns
    ]

    for column in date_columns:
        parsed_dates = pd.to_datetime(
            df[column],
            errors="coerce"
        )

        invalid_format_mask = (
            df[column].notna()
            & parsed_dates.isna()
        )

        print(f"\n{column}")
        print(f"Missing values: {int(df[column].isna().sum())}")
        print(
            "Invalid date formats:",
            int(invalid_format_mask.sum())
        )

        if invalid_format_mask.any():
            print(
                df.loc[
                    invalid_format_mask,
                    ["learner_id", column]
                ].to_string(index=False)
            )


# ============================================================
# EMPLOYER REQUIREMENTS AUDIT
# ============================================================

def inspect_employer_requirements(
    file_path: Path
) -> None:
    """
    Inspect employer requirements without modifying the JSON.
    """

    print("\n" + "=" * 60)
    print("EMPLOYER REQUIREMENTS INSPECTION")
    print("=" * 60)

    if not file_path.exists():
        print(f"ERROR: JSON file not found: {file_path}")
        return

    try:
        with file_path.open(
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError(
                "Expected the JSON top-level value to be an object."
            )

        requirements = data.get("employer_requirements")

        if not isinstance(requirements, list):
            raise ValueError(
                "'employer_requirements' must be a JSON list."
            )

        print(f"\nFile: {file_path.name}")
        print(f"Number of requirements: {len(requirements)}")

        if requirements:
            print("\nFirst requirement:")
            print(
                json.dumps(
                    requirements[0],
                    indent=2,
                    ensure_ascii=False
                )
            )

        role_ids = [
            item.get("role_id")
            for item in requirements
            if isinstance(item, dict)
        ]

        duplicate_role_ids = sorted({
            role_id
            for role_id in role_ids
            if role_id is not None
            and role_ids.count(role_id) > 1
        })

        print("\nDuplicate role IDs:")

        if duplicate_role_ids:
            print(duplicate_role_ids)
        else:
            print("None detected.")

    except Exception as error:
        print(
            f"JSON inspection failed: "
            f"{type(error).__name__}: {error}"
        )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    print("\n" + "=" * 60)
    print("SPRINTS TALENT ANALYTICS")
    print("INITIAL DATA INSPECTION")
    print("=" * 60)

    try:
        cohort_df = load_cohort_data(CSV_PATH)
        audit_data_quality(cohort_df)

    except Exception as error:
        print(
            f"\nCSV inspection failed: "
            f"{type(error).__name__}: {error}"
        )

    inspect_employer_requirements(JSON_PATH)

    print("\n" + "=" * 60)
    print("INITIAL INSPECTION FINISHED")
    print("=" * 60)


if __name__ == "__main__":
    main()