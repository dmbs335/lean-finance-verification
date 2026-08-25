from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.prospective_backtest.errors import ValidationError
from tools.prospective_backtest.model import load_problem
from tools.prospective_backtest.solver import solve, verify

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "examples" / "prospective_backtest" / "controlled.json"


class ProspectiveBacktestAdmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = load_problem(PACKAGE)
        self.report = solve(self.problem)

    def _modified(self, mutate):
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / "package.json"
        raw = json.loads(PACKAGE.read_text(encoding="utf-8"))
        mutate(raw)
        path.write_text(json.dumps(raw), encoding="utf-8")
        return temporary, solve(load_problem(path))

    def test_controlled_matured_package_is_admitted(self) -> None:
        self.assertEqual(self.report["status"], "admitted-controlled")
        self.assertIsNotNone(self.report["certificate"])
        self.assertTrue(all([
            self.report["gates"]["preregistered_before_first_decision"],
            self.report["gates"]["all_contracts_unchanged"],
            self.report["gates"]["trial_ledger_exact"],
            self.report["gates"]["outcome_mature"],
            self.report["gates"]["outcome_pass"],
        ]))

    def test_absent_outcome_remains_pending(self) -> None:
        temporary, report = self._modified(
            lambda raw: raw.update(outcome=None)
        )
        try:
            self.assertEqual(report["status"], "pending")
            self.assertIsNone(report["certificate"])
        finally:
            temporary.cleanup()

    def test_post_hoc_registration_is_rejected(self) -> None:
        temporary, report = self._modified(
            lambda raw: raw["plan"].update(
                registered_at="2027-01-02T00:00:00Z"
            )
        )
        try:
            self.assertEqual(report["status"], "rejected")
            self.assertFalse(
                report["gates"]["preregistered_before_first_decision"]
            )
        finally:
            temporary.cleanup()

    def test_hidden_trial_is_rejected(self) -> None:
        temporary, report = self._modified(
            lambda raw: raw["execution"]["executed_trial_ids"].append(
                "hidden-trial"
            )
        )
        try:
            self.assertEqual(report["status"], "rejected")
            self.assertFalse(report["gates"]["trial_ledger_exact"])
        finally:
            temporary.cleanup()

    def test_cost_model_mutation_is_rejected(self) -> None:
        temporary, report = self._modified(
            lambda raw: raw["execution"].update(
                cost_model_sha256="f" * 64
            )
        )
        try:
            self.assertEqual(report["status"], "rejected")
            self.assertFalse(
                report["gates"]["contracts_unchanged"][
                    "cost_model_sha256"
                ]
            )
        finally:
            temporary.cleanup()

    def test_premature_presented_outcome_is_rejected(self) -> None:
        temporary, report = self._modified(
            lambda raw: raw["outcome"].update(
                available_at="2027-06-30T00:00:00Z"
            )
        )
        try:
            self.assertEqual(report["status"], "rejected")
            self.assertFalse(report["gates"]["outcome_mature"])
        finally:
            temporary.cleanup()

    def test_failed_strict_pit_is_rejected(self) -> None:
        temporary, report = self._modified(
            lambda raw: raw["outcome"].update(strict_pit_verified=False)
        )
        try:
            self.assertEqual(report["status"], "rejected")
            self.assertFalse(report["gates"]["outcome_pass"])
        finally:
            temporary.cleanup()

    def test_failed_lower_bound_is_rejected(self) -> None:
        temporary, report = self._modified(
            lambda raw: raw["outcome"].update(result_lcb_bps=2)
        )
        try:
            self.assertEqual(report["status"], "rejected")
            self.assertFalse(report["outcome"]["lower_bound_passed"])
        finally:
            temporary.cleanup()

    def test_tampered_report_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["status"] = "pending"
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.problem, tampered)

    def test_solver_is_deterministic(self) -> None:
        self.assertEqual(self.report, solve(self.problem))


if __name__ == "__main__":
    unittest.main()
