import csv
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "frontend" / "app" / "baby-growth-library.ts"
DASHBOARD = ROOT / "frontend" / "app" / "maya" / "dashboard.tsx"
ONBOARDING = ROOT / "frontend" / "app" / "maya" / "onboarding.tsx"
VISUALS = ROOT / "frontend" / "app" / "maya" / "visuals.tsx"
CATALOGUE = ROOT / "data" / "catalogues" / "fetal_size_comparisons.csv"


class MayaProductUiRestorationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library_source = LIBRARY.read_text(encoding="utf-8")
        cls.dashboard_source = DASHBOARD.read_text(encoding="utf-8")
        cls.onboarding_source = ONBOARDING.read_text(encoding="utf-8")
        cls.visuals_source = VISUALS.read_text(encoding="utf-8")

    def test_complete_41_week_library_is_contiguous(self):
        weeks = [int(value) for value in re.findall(r"^\s*row\((\d+),", self.library_source, re.MULTILINE)]
        self.assertEqual(weeks, list(range(1, 42)))

    def test_mapped_assets_and_complete_source_inventory_exist(self):
        assets = set(re.findall(r'"(/(?:babies|comparisons)/[^"]+\.png)"', self.library_source))
        assets.add("/baby-week-22.png")
        self.assertEqual(len(assets), 29)
        missing = [asset for asset in sorted(assets) if not (ROOT / "frontend" / "public" / asset.lstrip("/")).is_file()]
        self.assertEqual(missing, [])

        public = ROOT / "frontend" / "public"
        self.assertEqual(len(list((public / "comparisons").glob("*.png"))), 25)
        self.assertEqual(len(list((public / "babies").glob("*.png"))), 5)
        self.assertTrue((public / "baby-week-22.png").is_file())

    def test_product_approved_week_set_matches_governed_catalogue(self):
        with CATALOGUE.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        expected = {
            int(json.loads(row["applies_to"])["start"])
            for row in rows
            if json.loads(row["applies_to"]).get("stage") == "pregnancy"
            and json.loads(row["details"]).get("editorial_review_status") == "product_approved_2026-09-11"
            and 1 <= int(json.loads(row["applies_to"])["start"]) <= 41
        }
        match = re.search(r"productApprovedWeeks = new Set\(\[([^]]+)]\)", self.library_source)
        self.assertIsNotNone(match)
        actual = {int(value.strip()) for value in match.group(1).split(",")}
        self.assertEqual(actual, expected)

    def test_rounded_later_week_sequence_is_preserved(self):
        required = {
            24: "Small muskmelon (kharbuja)",
            25: "Small muskmelon (kharbuja)",
            26: "Small cabbage",
            28: "Cabbage",
            29: "Cabbage",
            31: "Honeydew melon",
            32: "Honeydew melon",
            33: "Small watermelon",
            36: "Large muskmelon",
            40: "Full-size watermelon",
            41: "Large watermelon",
        }
        for week, label in required.items():
            self.assertIn(f'row({week}, "{label}"', self.library_source)
        self.assertNotRegex(self.library_source.lower(), r"banana|carrot")

    def test_only_source_linked_general_measurements_enter_dashboard(self):
        self.assertIn("measurementReviewState", self.library_source)
        self.assertIn("measurementSourceId", self.library_source)
        self.assertIn("imageOwnershipOrLicence", self.library_source)
        self.assertNotIn("measurementLength", self.dashboard_source)
        self.assertNotIn("measurementWeight", self.dashboard_source)
        self.assertIn('getGrowthMeasurements(preview.exact_week)', self.dashboard_source)
        self.assertIn("Approx. length", self.dashboard_source)
        self.assertIn("Approx. weight", self.dashboard_source)
        self.assertIn("Visual estimates only; your scan is your baby’s individual reference.", self.dashboard_source)
        self.assertIn("NHS week 6 guide", self.library_source)
        self.assertIn("NHS week 26 guide", self.library_source)

    def test_month_never_uses_client_side_week_guess(self):
        self.assertNotIn("4.345", self.onboarding_source)
        self.assertIn("will remain an approximate week range", self.onboarding_source)
        self.assertIn("range_confirmation", self.dashboard_source)

    def test_postpartum_dashboard_has_no_fetal_comparison(self):
        postpartum = self.dashboard_source.split("export function PostpartumDashboard", 1)[1].split("export function WeekLibrary", 1)[0]
        self.assertNotIn("PregnancyComparison", postpartum)
        self.assertNotIn("FetalVisual", postpartum)
        self.assertNotIn("FruitVisual", postpartum)

    def test_internal_review_labels_do_not_replace_growth_information(self):
        self.assertNotIn("Product direction accepted", self.dashboard_source)
        self.assertNotIn("Product review pending", self.dashboard_source)
        self.assertIn("measurementReviewState", self.library_source)
        self.assertIn("measurementSourceId", self.library_source)
        self.assertIn("Visual estimates only; your scan is your baby’s individual reference.", self.dashboard_source)

    def test_restart_requires_explicit_onboarding_and_keeps_recovery_in_memory(self):
        page_source = (ROOT / "frontend" / "app" / "page.tsx").read_text(encoding="utf-8")
        self.assertNotIn("sessionStorage.setItem", page_source)
        self.assertNotIn("localStorage.setItem", page_source)
        self.assertIn("lastPayload", page_source)
        self.assertIn("reason.isMissingSession", page_source)

    def test_complete_navigation_and_product_wording_are_present(self):
        for label in (
            "This week", "Nutrition", "Movement", "Symptoms", "Self-love",
            "FAQs", "Plans", "Recovery", "Nourishment", "Feeding",
        ):
            self.assertIn(f'"{label}"', self.dashboard_source)
        self.assertNotIn('["documents", "Care records"]', self.dashboard_source)
        combined = self.dashboard_source + self.onboarding_source + self.visuals_source
        self.assertIn("Capstone Product Preview", combined)
        self.assertNotIn("CONTROLLED FICTIONAL DEMO", combined)
        self.assertNotIn("CONTROLLED DEMO", combined)


if __name__ == "__main__":
    unittest.main()
