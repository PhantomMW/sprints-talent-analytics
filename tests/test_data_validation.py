import unittest
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CLEAN_DATA_PATH = PROJECT_ROOT / "data" / "sprints_cohort_clean.csv"
FEATURES_DATA_PATH = PROJECT_ROOT / "data" / "sprints_cohort_features.csv"


class TestDataValidation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not CLEAN_DATA_PATH.exists():
            raise FileNotFoundError(
                f"Clean dataset not found: {CLEAN_DATA_PATH}"
            )

        if not FEATURES_DATA_PATH.exists():
            raise FileNotFoundError(
                f"Feature dataset not found: {FEATURES_DATA_PATH}"
            )

        cls.clean_df = pd.read_csv(CLEAN_DATA_PATH)
        cls.features_df = pd.read_csv(FEATURES_DATA_PATH)

    def test_clean_dataset_has_24_records(self):
        self.assertEqual(
            len(self.clean_df),
            24,
            "The clean dataset should contain 24 records."
        )

    def test_clean_dataset_has_18_columns(self):
        self.assertEqual(
            len(self.clean_df.columns),
            18,
            "The clean dataset should contain 18 columns."
        )

    def test_learner_ids_are_unique(self):
        self.assertIn("learner_id", self.clean_df.columns)

        self.assertFalse(
            self.clean_df["learner_id"].duplicated().any(),
            "Duplicate learner IDs were found in the clean dataset."
        )

    def test_feature_dataset_has_24_records(self):
        self.assertEqual(
            len(self.features_df),
            24,
            "The feature dataset should contain 24 records."
        )

    def test_engineered_features_exist(self):
        expected_features = {
            "average_module_score",
            "module_score_count",
            "module_score_std",
            "enrollment_year",
            "days_to_graduation",
        }

        missing_features = expected_features - set(
            self.features_df.columns
        )

        self.assertFalse(
            missing_features,
            f"Missing engineered features: {sorted(missing_features)}"
        )

    def test_module_score_count_is_between_0_and_10(self):
        counts = self.features_df["module_score_count"].dropna()

        self.assertTrue(
            counts.between(0, 10).all(),
            "Module score counts must be between 0 and 10."
        )

    def test_graduation_duration_is_not_negative(self):
        durations = self.features_df["days_to_graduation"].dropna()

        self.assertTrue(
            (durations >= 0).all(),
            "Negative graduation durations were found."
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)