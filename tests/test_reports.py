import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "reports"


class TestReports(unittest.TestCase):

    def load_json_report(self, filename):
        report_path = REPORTS_DIR / filename

        self.assertTrue(
            report_path.exists(),
            f"Report does not exist: {filename}"
        )

        with report_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def test_cleaning_report_is_valid_json(self):
        report = self.load_json_report("cleaning_report.json")
        self.assertIsInstance(report, dict)

    def test_eda_summary_is_valid_json(self):
        report = self.load_json_report("eda_summary.json")
        self.assertIsInstance(report, dict)

    def test_employer_requirements_report_is_valid_json(self):
        report = self.load_json_report(
            "employer_requirements_summary.json"
        )
        self.assertIsInstance(report, dict)

    def test_feature_engineering_report_is_valid_json(self):
        report = self.load_json_report(
            "feature_engineering_report.json"
        )
        self.assertIsInstance(report, dict)

    def test_feature_engineering_readiness_is_valid_json(self):
        report = self.load_json_report(
            "feature_engineering_readiness.json"
        )
        self.assertIsInstance(report, dict)

    def test_employer_report_has_50_roles(self):
        report = self.load_json_report(
            "employer_requirements_summary.json"
        )

        self.assertEqual(report["total_requirement_records"], 50)

    def test_all_role_ids_are_unique(self):
        report = self.load_json_report(
            "employer_requirements_summary.json"
        )

        validation = report["role_id_validation"]

        self.assertEqual(validation["total_records"], 50)
        self.assertEqual(validation["records_with_role_id"], 50)
        self.assertEqual(validation["missing_role_id_records"], 0)
        self.assertEqual(validation["unique_role_ids"], 50)
        self.assertEqual(validation["duplicate_role_ids"], {})

    def test_all_roles_have_required_skills(self):
        report = self.load_json_report(
            "employer_requirements_summary.json"
        )

        skills = report["skills"]

        self.assertEqual(skills["roles_without_skills"], 0)
        self.assertEqual(skills["malformed_skill_lists"], 0)

    def test_python_is_required_by_all_50_roles(self):
        report = self.load_json_report(
            "employer_requirements_summary.json"
        )

        skill_frequency = report["skills"]["skill_frequency"]

        self.assertEqual(skill_frequency.get("Python"), 50)

    def test_company_tier_counts_sum_to_50(self):
        report = self.load_json_report(
            "employer_requirements_summary.json"
        )

        tier_counts = report["category_summaries"]["company_tier"]

        self.assertEqual(sum(tier_counts.values()), 50)
        self.assertEqual(tier_counts["Tier 1"], 20)
        self.assertEqual(tier_counts["Tier 2"], 19)
        self.assertEqual(tier_counts["Tier 3"], 11)

    def test_consistency_checks_pass(self):
        report = self.load_json_report(
            "employer_requirements_summary.json"
        )

        checks = report["consistency_checks"]

        expected_checks = [
            "all_records_have_role_id",
            "all_role_ids_are_unique",
            "all_records_have_required_skills",
            "all_records_have_job_title",
            "all_records_have_company_tier",
        ]

        for check in expected_checks:
            with self.subTest(check=check):
                self.assertIs(
                    checks[check],
                    True,
                    f"Consistency check failed: {check}"
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)