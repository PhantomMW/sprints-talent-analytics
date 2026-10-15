from pathlib import Path
import csv

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CSV_PATH = (
    PROJECT_ROOT
    / "data"
    / "sprints_cohort_data_2023.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_cohort_data(file_path: Path) -> pd.DataFrame:
    """
    Load the cohort CSV while removing only extra trailing
    empty fields that exceed the header width.

    The source file is never modified.
    """

    if not file_path.exists():
        raise FileNotFoundError(
            f"CSV file not found: {file_path}"
        )

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        rows = list(csv.reader(file))

    if not rows:
        raise ValueError("The CSV file is empty.")

    header = rows[0]
    expected_columns = len(header)

    cleaned_rows = []

    for line_number, original_row in enumerate(
        rows[1:],
        start=2
    ):
        row = original_row.copy()

        while len(row) > expected_columns and row[-1] == "":
            row.pop()

        if len(row) != expected_columns:
            raise ValueError(
                f"Unexpected field count at line {line_number}: "
                f"expected {expected_columns}, got {len(row)}."
            )

        cleaned_rows.append(row)

    df = pd.DataFrame(
        cleaned_rows,
        columns=header
    )

    # Normalize blank cells for analysis only.
    df = df.replace(r"^\s*$", pd.NA, regex=True)

    return df


# ============================================================
# DUPLICATE ANALYSIS
# ============================================================

def analyze_duplicates(df: pd.DataFrame) -> None:
    print("\n" + "=" * 65)
    print("DUPLICATE RECORD ANALYSIS")
    print("=" * 65)

    duplicate_mask = df.duplicated(keep=False)

    duplicate_records = df.loc[
        duplicate_mask
    ].sort_values("learner_id")

    print("\nTotal records:", len(df))
    print(
        "Rows belonging to duplicate groups:",
        int(duplicate_mask.sum())
    )
    print(
        "Extra duplicate rows:",
        int(df.duplicated().sum())
    )

    if duplicate_records.empty:
        print("\nNo fully duplicated records found.")
    else:
        print("\nDuplicated records:")
        print(
            duplicate_records.to_string(index=False)
        )

    print("\nDuplicate learner ID counts:")

    learner_counts = df["learner_id"].value_counts()

    repeated_ids = learner_counts[
        learner_counts > 1
    ]

    if repeated_ids.empty:
        print("No duplicate learner IDs.")
    else:
        print(repeated_ids.to_string())


# ============================================================
# MISSING VALUE ANALYSIS
# ============================================================

def analyze_missing_values(df: pd.DataFrame) -> None:
    print("\n" + "=" * 65)
    print("MISSING VALUE ANALYSIS")
    print("=" * 65)

    missing_counts = df.isna().sum()

    missing_summary = pd.DataFrame({
        "missing_count": missing_counts,
        "missing_percentage": (
            missing_counts / len(df) * 100
        ).round(2)
    })

    missing_summary = missing_summary[
        missing_summary["missing_count"] > 0
    ].sort_values(
        "missing_count",
        ascending=False
    )

    if missing_summary.empty:
        print("\nNo missing values detected.")
    else:
        print("\nMissing values by column:")
        print(missing_summary.to_string())

    print(
        "\nTotal missing cells:",
        int(df.isna().sum().sum())
    )

    # Show records with at least one missing field.
    records_with_missing = df[
        df.isna().any(axis=1)
    ]

    print(
        "\nRecords containing missing values:",
        len(records_with_missing)
    )

    if not records_with_missing.empty:
        print(
            records_with_missing[
                [
                    "learner_id",
                    "graduation_date",
                    "engagement_score",
                    "module_1_score",
                    "module_2_score",
                    "module_3_score",
                    "module_4_score",
                    "module_5_score",
                    "module_6_score",
                    "module_7_score",
                    "module_8_score",
                    "module_9_score",
                    "module_10_score",
                    "capstone_score"
                ]
            ].to_string(index=False)
        )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    print("=" * 65)
    print("SPRINTS TALENT ANALYTICS")
    print("DETAILED DATA QUALITY INVESTIGATION")
    print("=" * 65)

    df = load_cohort_data(CSV_PATH)

    analyze_duplicates(df)

    analyze_missing_values(df)

    print("\n" + "=" * 65)
    print("DETAILED INVESTIGATION FINISHED")
    print("=" * 65)


if __name__ == "__main__":
    main()