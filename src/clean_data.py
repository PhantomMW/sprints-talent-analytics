from pathlib import Path
import csv
import json

import pandas as pd


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"

INPUT_CSV = DATA_DIR / "sprints_cohort_data_2023.csv"
OUTPUT_CSV = DATA_DIR / "sprints_cohort_clean.csv"
CLEANING_REPORT = REPORTS_DIR / "cleaning_report.json"

# Provisional assumption: engagement is expected to be 0-100.
ENGAGEMENT_MIN = 0
ENGAGEMENT_MAX = 100


# ============================================================
# LOAD SOURCE DATA
# ============================================================

def load_source_data(file_path: Path) -> pd.DataFrame:
    """
    Read the original CSV and repair only extra trailing empty
    fields that exceed the header width.

    The source CSV is never modified.
    """

    if not file_path.exists():
        raise FileNotFoundError(
            f"Source CSV not found: {file_path}"
        )

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        rows = list(csv.reader(file))

    if not rows:
        raise ValueError("The source CSV is empty.")

    header = rows[0]
    expected_columns = len(header)

    if len(header) != len(set(header)):
        raise ValueError(
            "Duplicate column names detected in the CSV header."
        )

    records = []
    repaired_rows = []

    for line_number, original_row in enumerate(
        rows[1:],
        start=2
    ):
        row = original_row.copy()
        original_count = len(row)

        # Repair only extra trailing empty fields.
        while len(row) > expected_columns and row[-1] == "":
            row.pop()

        if len(row) != expected_columns:
            raise ValueError(
                f"Line {line_number} contains {len(row)} fields; "
                f"expected {expected_columns}."
            )

        if len(row) != original_count:
            repaired_rows.append({
                "line_number": line_number,
                "learner_id": row[0] if row else None,
                "original_fields": original_count,
                "final_fields": len(row),
            })

        records.append(row)

    df = pd.DataFrame(records, columns=header)

    # Normalize blank cells.
    df = df.replace(r"^\s*$", pd.NA, regex=True)

    return df, repaired_rows


# ============================================================
# CLEANING
# ============================================================

def clean_data(
    source_df: pd.DataFrame
) -> tuple[pd.DataFrame, dict]:
    """
    Clean a copy of the source data and record every cleaning
    operation in a structured report.
    """

    df = source_df.copy(deep=True)

    report = {
        "input_records": int(len(df)),
        "input_columns": int(len(df.columns)),
        "structural_repairs": [],
        "duplicate_rows_removed": 0,
        "invalid_engagement_values": [],
        "numeric_conversion_failures": {},
        "date_conversion_failures": {},
        "missing_values_before_cleaning": {},
        "missing_values_after_cleaning": {},
        "output_records": 0,
        "output_columns": int(len(df.columns)),
    }

    # --------------------------------------------------------
    # 1. Record missing values before cleaning
    # --------------------------------------------------------

    report["missing_values_before_cleaning"] = {
        column: int(count)
        for column, count in df.isna().sum().items()
    }

    # --------------------------------------------------------
    # 2. Remove exact duplicate rows
    # --------------------------------------------------------

    duplicate_mask = df.duplicated(keep="first")

    report["duplicate_rows_removed"] = int(
        duplicate_mask.sum()
    )

    df = df.drop_duplicates(keep="first").copy()

    # --------------------------------------------------------
    # 3. Convert numeric columns
    # --------------------------------------------------------

    score_columns = [
        column
        for column in df.columns
        if column.endswith("_score")
    ]

    for column in score_columns:
        original_values = df[column].copy()

        converted_values = pd.to_numeric(
            original_values,
            errors="coerce"
        )

        failed_mask = (
            original_values.notna()
            & converted_values.isna()
        )

        report["numeric_conversion_failures"][column] = int(
            failed_mask.sum()
        )

        df[column] = converted_values

    # --------------------------------------------------------
    # 4. Validate engagement score range
    # --------------------------------------------------------

    if "engagement_score" in df.columns:
        engagement = df["engagement_score"]

        invalid_mask = (
            (engagement < ENGAGEMENT_MIN)
            | (engagement > ENGAGEMENT_MAX)
        )

        invalid_rows = df.loc[
            invalid_mask,
            ["learner_id", "engagement_score"]
        ]

        report["invalid_engagement_values"] = [
            {
                "learner_id": str(row["learner_id"]),
                "original_value": float(row["engagement_score"]),
                "action": "Converted to missing value",
            }
            for _, row in invalid_rows.iterrows()
        ]

        # Preserve invalid original values in the report,
        # but mark them missing in the cleaned dataset.
        df.loc[invalid_mask, "engagement_score"] = pd.NA

    # --------------------------------------------------------
    # 5. Convert date columns
    # --------------------------------------------------------

    date_columns = [
        column
        for column in [
            "enrollment_date",
            "graduation_date"
        ]
        if column in df.columns
    ]

    for column in date_columns:
        original_values = df[column].copy()

        converted_values = pd.to_datetime(
            original_values,
            errors="coerce",
            format="%Y-%m-%d"
        )

        failed_mask = (
            original_values.notna()
            & converted_values.isna()
        )

        report["date_conversion_failures"][column] = int(
            failed_mask.sum()
        )

        df[column] = converted_values

    # --------------------------------------------------------
    # 6. Record missing values after cleaning
    # --------------------------------------------------------

    report["missing_values_after_cleaning"] = {
        column: int(count)
        for column, count in df.isna().sum().items()
    }

    report["output_records"] = int(len(df))

    return df, report


# ============================================================
# SAVE OUTPUTS
# ============================================================

def save_outputs(
    cleaned_df: pd.DataFrame,
    report: dict
) -> None:
    """
    Save the cleaned dataset and a JSON cleaning report.
    """

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    cleaned_df.to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8-sig",
        date_format="%Y-%m-%d"
    )

    with CLEANING_REPORT.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False
        )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    print("=" * 65)
    print("SPRINTS TALENT ANALYTICS")
    print("DATA CLEANING PIPELINE")
    print("=" * 65)

    source_df, repaired_rows = load_source_data(INPUT_CSV)

    cleaned_df, report = clean_data(source_df)

    report["structural_repairs"] = repaired_rows

    save_outputs(cleaned_df, report)

    print("\nCLEANING SUMMARY")
    print("-" * 65)

    print(f"Original records: {report['input_records']}")
    print(f"Cleaned records: {report['output_records']}")

    print(
        "Duplicate rows removed:",
        report["duplicate_rows_removed"]
    )

    print(
        "Structural repairs:",
        len(report["structural_repairs"])
    )

    print(
        "Invalid engagement values:",
        len(report["invalid_engagement_values"])
    )

    print("\nMissing values after cleaning:")

    for column, count in (
        report["missing_values_after_cleaning"].items()
    ):
        if count > 0:
            print(f"{column}: {count}")

    print("\nOutput files:")
    print(OUTPUT_CSV)
    print(CLEANING_REPORT)

    print("\nSource CSV was not modified.")
    print("Cleaning pipeline finished.")


if __name__ == "__main__":
    main()