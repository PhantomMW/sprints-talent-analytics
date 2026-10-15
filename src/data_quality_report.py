from pathlib import Path
import csv

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CSV_PATH = (
    PROJECT_ROOT
    / "data"
    / "sprints_cohort_data_2023.csv"
)


def load_data(file_path: Path) -> pd.DataFrame:
    """Load CSV without modifying the original file."""

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        rows = list(csv.reader(file))

    if not rows:
        raise ValueError("CSV file is empty.")

    columns = rows[0]
    records = []

    for line_number, original_row in enumerate(
        rows[1:],
        start=2
    ):
        row = original_row.copy()

        while len(row) > len(columns) and row[-1] == "":
            row.pop()

        if len(row) != len(columns):
            raise ValueError(
                f"Invalid field count at line {line_number}."
            )

        records.append(row)

    df = pd.DataFrame(records, columns=columns)

    return df.replace(r"^\s*$", pd.NA, regex=True)


def create_quality_report(df: pd.DataFrame) -> pd.DataFrame:
    """Create a summary of data quality issues."""

    report = []

    report.append({
        "category": "Dataset",
        "metric": "Total records",
        "value": len(df),
        "details": "Records loaded from the original CSV"
    })

    report.append({
        "category": "Dataset",
        "metric": "Total columns",
        "value": len(df.columns),
        "details": "Columns in the original CSV"
    })

    report.append({
        "category": "Duplicates",
        "metric": "Extra duplicate rows",
        "value": int(df.duplicated().sum()),
        "details": "Exact duplicate rows beyond the first occurrence"
    })

    report.append({
        "category": "Duplicates",
        "metric": "Rows with repeated learner IDs",
        "value": int(
            df["learner_id"].duplicated(keep=False).sum()
        ),
        "details": "Rows sharing a learner ID with another row"
    })

    for column in df.columns:
        missing_count = int(df[column].isna().sum())

        if missing_count > 0:
            report.append({
                "category": "Missing values",
                "metric": column,
                "value": missing_count,
                "details": (
                    f"{missing_count / len(df) * 100:.2f}% "
                    "of records have missing values"
                )
            })

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

        invalid_count = int(
            invalid_mask.fillna(False).sum()
        )

        if invalid_count > 0:
            report.append({
                "category": "Invalid scores",
                "metric": column,
                "value": invalid_count,
                "details": "Values outside the assumed 0-100 range"
            })

    return pd.DataFrame(report)


def main() -> None:
    print("=" * 60)
    print("DATA QUALITY REPORT")
    print("=" * 60)

    df = load_data(CSV_PATH)

    report = create_quality_report(df)

    print(report.to_string(index=False))

    print("\nReport generated in memory only.")
    print("No source data has been modified.")


if __name__ == "__main__":
    main()