import json
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# SPRINTS TALENT ANALYTICS
# Exploratory Data Analysis (EDA)
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = ROOT_DIR / "data" / "sprints_cohort_clean.csv"
REPORT_PATH = ROOT_DIR / "reports" / "eda_summary.json"


def load_clean_data():
    """Load the cleaned dataset and prepare data types."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Clean dataset not found: {DATA_PATH}\n"
            "Run src/clean_data.py first."
        )

    df = pd.read_csv(DATA_PATH)

    # Convert date columns to datetime.
    date_columns = ["enrollment_date", "graduation_date"]

    for column in date_columns:
        if column in df.columns:
            df[column] = pd.to_datetime(
                df[column],
                errors="coerce",
                format="%Y-%m-%d",
            )

    # Convert score columns to numeric.
    score_columns = [
        column
        for column in df.columns
        if column.endswith("_score")
    ]

    for column in score_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    return df, score_columns


def summarize_categorical_column(df, column):
    """Summarize the distribution of a categorical column."""

    counts = df[column].value_counts(dropna=False)

    result = {}

    for value, count in counts.items():
        label = "Missing" if pd.isna(value) else str(value)

        result[label] = {
            "count": int(count),
            "percentage": round(
                float(count / len(df) * 100),
                2,
            ),
        }

    return result


def summarize_scores(df, score_columns):
    """Calculate descriptive statistics for all score columns."""

    score_summary = {}

    for column in score_columns:
        values = df[column].dropna()

        score_summary[column] = {
            "valid_count": int(values.count()),
            "missing_count": int(df[column].isna().sum()),
            "mean": (
                round(float(values.mean()), 2)
                if not values.empty
                else None
            ),
            "median": (
                round(float(values.median()), 2)
                if not values.empty
                else None
            ),
            "standard_deviation": (
                round(float(values.std()), 2)
                if len(values) > 1
                else None
            ),
            "minimum": (
                round(float(values.min()), 2)
                if not values.empty
                else None
            ),
            "maximum": (
                round(float(values.max()), 2)
                if not values.empty
                else None
            ),
        }

    return score_summary


def analyze_relationship(df, first_column, second_column):
    """Analyze the correlation between two numeric columns."""

    valid_data = df[[first_column, second_column]].dropna()

    result = {
        "first_variable": first_column,
        "second_variable": second_column,
        "valid_pairs": int(len(valid_data)),
        "correlation": None,
        "interpretation": "Insufficient data",
    }

    if len(valid_data) < 2:
        return result

    first_values = valid_data[first_column]
    second_values = valid_data[second_column]

    # Correlation is undefined when either variable is constant.
    if (
        first_values.nunique() < 2
        or second_values.nunique() < 2
    ):
        result["interpretation"] = (
            "Correlation is undefined because a variable is constant."
        )
        return result

    correlation = first_values.corr(second_values)

    if pd.isna(correlation):
        return result

    correlation = float(correlation)

    result["correlation"] = round(correlation, 3)

    absolute_correlation = abs(correlation)

    if absolute_correlation < 0.2:
        strength = "very weak"
    elif absolute_correlation < 0.4:
        strength = "weak"
    elif absolute_correlation < 0.6:
        strength = "moderate"
    elif absolute_correlation < 0.8:
        strength = "strong"
    else:
        strength = "very strong"

    direction = (
        "positive"
        if correlation > 0
        else "negative"
    )

    result["interpretation"] = (
        f"{strength} {direction} correlation"
    )

    return result


def analyze_data_completeness(df):
    """Calculate record-level and column-level completeness."""

    total_columns = len(df.columns)

    completeness = {}

    for _, row in df.iterrows():
        learner_id = str(row["learner_id"])

        available_values = int(row.notna().sum())

        completeness[learner_id] = {
            "available_values": available_values,
            "missing_values": int(row.isna().sum()),
            "completeness_percentage": round(
                available_values / total_columns * 100,
                2,
            ),
        }

    column_completeness = {}

    for column in df.columns:
        available = int(df[column].notna().sum())

        column_completeness[column] = {
            "available_values": available,
            "missing_values": int(df[column].isna().sum()),
            "completeness_percentage": round(
                available / len(df) * 100,
                2,
            ),
        }

    return {
        "records": completeness,
        "columns": column_completeness,
    }


def analyze_completion(df):
    """Summarize graduation date availability."""

    total_learners = len(df)
    graduated = int(df["graduation_date"].notna().sum())
    missing_graduation_date = int(
        df["graduation_date"].isna().sum()
    )

    result = {
        "total_learners": total_learners,
        "records_with_graduation_date": graduated,
        "records_missing_graduation_date": missing_graduation_date,
        "graduation_date_available_percentage": round(
            graduated / total_learners * 100,
            2,
        ) if total_learners else None,
    }

    if "capstone_score" in df.columns:
        result["learners_with_capstone_score"] = int(
            df["capstone_score"].notna().sum()
        )

        result["learners_missing_capstone_score"] = int(
            df["capstone_score"].isna().sum()
        )

    return result


def main():
    print("=" * 65)
    print("SPRINTS TALENT ANALYTICS")
    print("EXPLORATORY DATA ANALYSIS")
    print("=" * 65)

    df, score_columns = load_clean_data()

    # --------------------------------------------------------
    # 1. Dataset overview
    # --------------------------------------------------------

    print("\n1. DATASET OVERVIEW")
    print("-" * 65)

    print(f"Records: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print(f"Duplicate rows: {int(df.duplicated().sum())}")

    print("\nColumn data types:")
    print(df.dtypes.to_string())

    # --------------------------------------------------------
    # 2. Cohort distribution
    # --------------------------------------------------------

    print("\n2. COHORT DISTRIBUTION")
    print("-" * 65)

    cohort_distribution = summarize_categorical_column(
        df,
        "cohort_id",
    )

    print(
        pd.Series(
            {
                cohort: values["count"]
                for cohort, values in cohort_distribution.items()
            }
        ).to_string()
    )

    # --------------------------------------------------------
    # 3. Track distribution
    # --------------------------------------------------------

    print("\n3. TRACK DISTRIBUTION")
    print("-" * 65)

    track_distribution = summarize_categorical_column(
        df,
        "track_name",
    )

    print(
        pd.Series(
            {
                track: values["count"]
                for track, values in track_distribution.items()
            }
        ).to_string()
    )

    # --------------------------------------------------------
    # 4. Score statistics
    # --------------------------------------------------------

    print("\n4. SCORE STATISTICS")
    print("-" * 65)

    score_summary = summarize_scores(
        df,
        score_columns,
    )

    score_table = pd.DataFrame(score_summary).T

    print(score_table.to_string())

    # --------------------------------------------------------
    # 5. Engagement analysis
    # --------------------------------------------------------

    print("\n5. ENGAGEMENT ANALYSIS")
    print("-" * 65)

    engagement = df["engagement_score"].dropna()

    engagement_summary = {
        "valid_count": int(engagement.count()),
        "missing_count": int(df["engagement_score"].isna().sum()),
        "mean": (
            round(float(engagement.mean()), 2)
            if not engagement.empty
            else None
        ),
        "median": (
            round(float(engagement.median()), 2)
            if not engagement.empty
            else None
        ),
        "minimum": (
            round(float(engagement.min()), 2)
            if not engagement.empty
            else None
        ),
        "maximum": (
            round(float(engagement.max()), 2)
            if not engagement.empty
            else None
        ),
    }

    print(json.dumps(engagement_summary, indent=2))

    # --------------------------------------------------------
    # 6. Relationship analysis
    # --------------------------------------------------------

    print("\n6. ENGAGEMENT AND CAPSTONE RELATIONSHIP")
    print("-" * 65)

    engagement_capstone = analyze_relationship(
        df,
        "engagement_score",
        "capstone_score",
    )

    print(json.dumps(engagement_capstone, indent=2))

    # --------------------------------------------------------
    # 7. Module and capstone comparison
    # --------------------------------------------------------

    print("\n7. MODULE AND CAPSTONE MEANS")
    print("-" * 65)

    module_columns = [
        column
        for column in score_columns
        if column.startswith("module_")
    ]

    module_means = {}

    for column in module_columns:
        value = df[column].mean()

        module_means[column] = (
            round(float(value), 2)
            if pd.notna(value)
            else None
        )

    capstone_mean = df["capstone_score"].mean()

    module_comparison = {
        "module_means": module_means,
        "capstone_mean": (
            round(float(capstone_mean), 2)
            if pd.notna(capstone_mean)
            else None
        ),
    }

    print(
        pd.Series(module_means).to_string()
    )

    print(f"\nCapstone mean: {module_comparison['capstone_mean']}")

    # --------------------------------------------------------
    # 8. Completion and missing data
    # --------------------------------------------------------

    print("\n8. COMPLETION SUMMARY")
    print("-" * 65)

    completion_summary = analyze_completion(df)

    print(json.dumps(completion_summary, indent=2))

    print("\n9. MISSING VALUES BY COLUMN")
    print("-" * 65)

    missing_values = df.isna().sum()

    print(missing_values[missing_values > 0].to_string())

    # --------------------------------------------------------
    # 10. Build and save the EDA report
    # --------------------------------------------------------

    report = {
        "dataset_overview": {
            "records": int(len(df)),
            "columns": int(len(df.columns)),
            "duplicate_rows": int(df.duplicated().sum()),
            "column_names": list(df.columns),
            "data_types": {
                column: str(dtype)
                for column, dtype in df.dtypes.items()
            },
        },
        "cohort_distribution": cohort_distribution,
        "track_distribution": track_distribution,
        "score_statistics": score_summary,
        "engagement_summary": engagement_summary,
        "engagement_capstone_relationship": engagement_capstone,
        "module_comparison": module_comparison,
        "completion_summary": completion_summary,
        "data_completeness": analyze_data_completeness(df),
        "missing_values_by_column": {
            column: int(count)
            for column, count in missing_values.items()
        },
    }

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(REPORT_PATH, "w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )

    print("\n" + "=" * 65)
    print("EDA COMPLETED SUCCESSFULLY")
    print("=" * 65)
    print(f"Report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()