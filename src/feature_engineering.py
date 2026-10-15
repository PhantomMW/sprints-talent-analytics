import json
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# SPRINTS TALENT ANALYTICS
# Feature Engineering Pipeline
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    ROOT_DIR
    / "data"
    / "sprints_cohort_clean.csv"
)

OUTPUT_PATH = (
    ROOT_DIR
    / "data"
    / "sprints_cohort_features.csv"
)

REPORT_PATH = (
    ROOT_DIR
    / "reports"
    / "feature_engineering_report.json"
)


MODULE_COLUMNS = [
    f"module_{number}_score"
    for number in range(1, 11)
]


DATE_COLUMNS = [
    "enrollment_date",
    "graduation_date",
]


def load_data():
    """Load cleaned learner data and validate required columns."""

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Clean dataset not found: {INPUT_PATH}"
        )

    df = pd.read_csv(INPUT_PATH)

    required_columns = [
        "learner_id",
        *MODULE_COLUMNS,
        *DATE_COLUMNS,
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Required columns are missing: {missing_columns}"
        )

    for column in MODULE_COLUMNS:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    for column in DATE_COLUMNS:
        df[column] = pd.to_datetime(
            df[column],
            errors="coerce",
            format="%Y-%m-%d",
        )

    return df


def create_module_features(df):
    """Create learner-level features from available module scores."""

    module_scores = df[MODULE_COLUMNS]

    # Mean across available module scores.
    # Missing scores are ignored, not replaced with zero.
    df["average_module_score"] = module_scores.mean(
        axis=1,
        skipna=True,
    )

    # Number of module scores actually available.
    df["module_score_count"] = module_scores.count(
        axis=1,
    ).astype("int64")

    # Standard deviation requires at least two available scores.
    df["module_score_std"] = module_scores.std(
        axis=1,
        skipna=True,
        ddof=1,
    )

    # A learner with no module scores should have no average.
    df.loc[
        df["module_score_count"] == 0,
        "average_module_score",
    ] = np.nan

    return df


def create_date_features(df):
    """Create date-derived features without inventing missing dates."""

    df["enrollment_year"] = (
        df["enrollment_date"]
        .dt.year
        .astype("Int64")
    )

    graduation_days = (
        df["graduation_date"] - df["enrollment_date"]
    ).dt.days

    # Negative durations are invalid for this derived feature.
    invalid_duration_mask = graduation_days < 0

    df["days_to_graduation"] = graduation_days.astype("float64")

    df.loc[
        invalid_duration_mask,
        "days_to_graduation",
    ] = np.nan

    return df, int(invalid_duration_mask.sum())


def build_feature_report(
    original_df,
    featured_df,
    invalid_duration_count,
):
    """Build a JSON report documenting the derived features."""

    report = {
        "input_file": str(INPUT_PATH.relative_to(ROOT_DIR)),
        "output_file": str(OUTPUT_PATH.relative_to(ROOT_DIR)),
        "input_records": int(len(original_df)),
        "output_records": int(len(featured_df)),
        "input_columns": int(len(original_df.columns)),
        "output_columns": int(len(featured_df.columns)),
        "records_changed": int(
            len(original_df) != len(featured_df)
        ),
        "duplicate_rows_in_output": int(
            featured_df.duplicated().sum()
        ),
        "derived_features": {
            "average_module_score": {
                "description": (
                    "Mean of available module scores per learner."
                ),
                "missing_count": int(
                    featured_df["average_module_score"].isna().sum()
                ),
                "minimum": (
                    round(
                        float(
                            featured_df[
                                "average_module_score"
                            ].min()
                        ),
                        2,
                    )
                    if featured_df[
                        "average_module_score"
                    ].notna().any()
                    else None
                ),
                "maximum": (
                    round(
                        float(
                            featured_df[
                                "average_module_score"
                            ].max()
                        ),
                        2,
                    )
                    if featured_df[
                        "average_module_score"
                    ].notna().any()
                    else None
                ),
            },
            "module_score_count": {
                "description": (
                    "Count of non-missing module scores per learner."
                ),
                "minimum": int(
                    featured_df["module_score_count"].min()
                ),
                "maximum": int(
                    featured_df["module_score_count"].max()
                ),
            },
            "module_score_std": {
                "description": (
                    "Sample standard deviation of available "
                    "module scores per learner."
                ),
                "missing_count": int(
                    featured_df["module_score_std"].isna().sum()
                ),
            },
            "enrollment_year": {
                "description": (
                    "Year extracted from enrollment_date."
                ),
                "missing_count": int(
                    featured_df["enrollment_year"].isna().sum()
                ),
                "distribution": {
                    str(int(year)): int(count)
                    for year, count in (
                        featured_df["enrollment_year"]
                        .dropna()
                        .value_counts()
                        .sort_index()
                        .items()
                    )
                },
            },
            "days_to_graduation": {
                "description": (
                    "Days between enrollment and graduation, "
                    "when both dates are available and the "
                    "duration is non-negative."
                ),
                "missing_count": int(
                    featured_df["days_to_graduation"].isna().sum()
                ),
                "invalid_negative_durations": (
                    invalid_duration_count
                ),
                "minimum": (
                    int(
                        featured_df[
                            "days_to_graduation"
                        ].min()
                    )
                    if featured_df[
                        "days_to_graduation"
                    ].notna().any()
                    else None
                ),
                "maximum": (
                    int(
                        featured_df[
                            "days_to_graduation"
                        ].max()
                    )
                    if featured_df[
                        "days_to_graduation"
                    ].notna().any()
                    else None
                ),
            },
        },
        "missing_values_after_feature_engineering": {
            column: int(count)
            for column, count in featured_df.isna().sum().items()
        },
        "skill_mapping_status": (
            "Not performed. Module scores do not directly "
            "identify individual employer-required skills."
        ),
    }

    return report


def main():
    print("=" * 70)
    print("SPRINTS TALENT ANALYTICS")
    print("FEATURE ENGINEERING")
    print("=" * 70)

    original_df = load_data()

    original_record_count = len(original_df)

    print("\n1. INPUT DATA")
    print("-" * 70)

    print(f"Records: {len(original_df)}")
    print(f"Columns: {len(original_df.columns)}")

    # Create features on a separate copy.
    featured_df = original_df.copy()

    featured_df = create_module_features(featured_df)

    featured_df, invalid_duration_count = create_date_features(
        featured_df
    )

    # Ensure feature engineering has not changed the row count.
    if len(featured_df) != original_record_count:
        raise RuntimeError(
            "Feature engineering unexpectedly changed "
            "the number of records."
        )

    if featured_df["learner_id"].duplicated().any():
        raise RuntimeError(
            "Duplicate learner IDs were found in the feature dataset."
        )

    # --------------------------------------------------------
    # Save feature dataset
    # --------------------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    featured_df.to_csv(
        OUTPUT_PATH,
        index=False,
        date_format="%Y-%m-%d",
    )

    # --------------------------------------------------------
    # Build and save report
    # --------------------------------------------------------

    report = build_feature_report(
        original_df,
        featured_df,
        invalid_duration_count,
    )

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

    # --------------------------------------------------------
    # Print results
    # --------------------------------------------------------

    print("\n2. FEATURE ENGINEERING RESULTS")
    print("-" * 70)

    print(f"Output records: {len(featured_df)}")
    print(f"Output columns: {len(featured_df.columns)}")

    feature_columns = [
        "learner_id",
        "average_module_score",
        "module_score_count",
        "module_score_std",
        "enrollment_year",
        "days_to_graduation",
    ]

    print("\nSample of engineered features:")

    print(
        featured_df[feature_columns]
        .head(10)
        .to_string(index=False)
    )

    print("\n3. FEATURE VALIDATION")
    print("-" * 70)

    print(
        "Duplicate learner IDs:",
        int(featured_df["learner_id"].duplicated().sum()),
    )

    print(
        "Missing average module scores:",
        int(featured_df["average_module_score"].isna().sum()),
    )

    print(
        "Module score count range:",
        int(featured_df["module_score_count"].min()),
        "to",
        int(featured_df["module_score_count"].max()),
    )

    print(
        "Missing graduation durations:",
        int(featured_df["days_to_graduation"].isna().sum()),
    )

    print(
        "Invalid negative durations:",
        invalid_duration_count,
    )

    print("\n4. OUTPUT FILES")
    print("-" * 70)

    print(f"Feature dataset: {OUTPUT_PATH}")
    print(f"Feature report: {REPORT_PATH}")

    print("\n" + "=" * 70)
    print("FEATURE ENGINEERING COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()