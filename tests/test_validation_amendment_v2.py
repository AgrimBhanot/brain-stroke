"""Acceptance boundaries and failure retention for the Option 3 amendment."""
import json
from pathlib import Path
import tempfile
import unittest

from src.validate_registry_v2 import summarize_power, update_power_evidence, file_hash


class AmendmentTests(unittest.TestCase):
    plan = {"seed": 83000, "datasets": 200, "alpha": .05, "expected_rate": [.5, .95]}

    def rows(self, detected):
        return [{"seed": 83000 + i, "p": .04 if i < detected else .05, "failure_reason": None}
                for i in range(200)]

    def test_inclusive_rate_limits_and_strict_p(self):
        for count, passed in [(99, False), (100, True), (190, True), (191, False)]:
            with self.subTest(count=count):
                result = summarize_power(self.rows(count), self.plan)
                self.assertEqual(result["passed"], passed)
                self.assertEqual(result["detections"], count)

    def test_failures_and_duplicate_or_missing_seeds_fail_closed(self):
        rows = self.rows(150)
        for broken in (rows[:-1], rows[:-1] + [rows[0]],
                       rows[:-1] + [{"seed": 83199, "failure_reason": "failed"}]):
            result = summarize_power(broken, self.plan)
            self.assertFalse(result["passed"])
            self.assertIsNone(result["detection_rate"])

    def test_nonfinite_p_fails(self):
        rows = self.rows(150)
        rows[0]["p"] = float("nan")
        self.assertFalse(summarize_power(rows, self.plan)["passed"])

    def test_evidence_requires_gates_and_prior_checks_preserves_failures(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "docs").mkdir()
            output, null = root / "report.json", root / "null.json"
            output.write_text("{}")
            null.write_text("{}")
            evidence = {"controls": {"full_positive": {"passed": False},
                        "null_calibration": {"passed": True, "path": "null.json", "sha256": file_hash(null)}},
                        "unit_tests": {"total": 20, "passed": 20}, "shuffled_smoke": {"tests": 9, "completed": 9}}
            path = root / "docs/REGISTRY_VALIDATION_RESULTS.json"
            path.write_text(json.dumps(evidence))
            report = {"passed": False, "plan": {}, "gate_a": {"passed": True}, "gate_b": {"passed": False}}
            update_power_evidence(report, output, root)
            self.assertFalse(json.loads(path.read_text())["acceptance_passed"])
            report["passed"] = report["gate_b"]["passed"] = True
            update_power_evidence(report, output, root)
            result = json.loads(path.read_text())
            self.assertTrue(result["acceptance_passed"])
            self.assertFalse(result["controls"]["full_positive"]["passed"])
            null.write_text("tampered")
            update_power_evidence(report, output, root)
            self.assertFalse(json.loads(path.read_text())["acceptance_passed"])


if __name__ == "__main__":
    unittest.main()
