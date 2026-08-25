from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.anytime_policy_monitor.errors import ValidationError
from tools.anytime_policy_monitor.model import load_problem
from tools.anytime_policy_monitor.solver import solve, verify

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "examples" / "anytime_policy_monitor" / "mixture.json"


class AnytimePolicyMonitorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = load_problem(MODEL)
        self.report = solve(self.problem)

    def _counterfactual(self, mutate):
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / "model.json"
        raw = json.loads(MODEL.read_text(encoding="utf-8"))
        mutate(raw)
        path.write_text(json.dumps(raw), encoding="utf-8")
        return temporary, path

    def test_exact_mixture_crosses_at_seven(self) -> None:
        evidence = self.report["anytime_evidence"]
        self.assertEqual(evidence["first_crossing_observation"], 7)
        self.assertEqual(
            evidence["maximum_e_value"],
            {"numerator": 3917521, "denominator": 98304, "floor": 39},
        )
        self.assertTrue(evidence["crossed_threshold"])
        self.assertEqual(
            self.report["e_value_threshold"],
            {"numerator": 20, "denominator": 1, "floor": 20},
        )

    def test_prefix_six_has_not_crossed(self) -> None:
        self.assertFalse(
            self.report["observations"][5]["crossed_threshold"]
        )
        self.assertEqual(
            self.report["observations"][6]["mixture_e_value"],
            {"numerator": 98467, "denominator": 4096, "floor": 24},
        )

    def test_authority_advances_one_level(self) -> None:
        self.assertTrue(self.report["authority"]["eligible"])
        self.assertEqual(self.report["authority"]["current"], "recommend")
        self.assertEqual(
            self.report["authority"]["decision"], "microAutonomy"
        )
        self.assertEqual(self.report["authority"]["capital_cap"], 10)

    def test_nonpositive_sequence_does_not_cross(self) -> None:
        temporary, path = self._counterfactual(
            lambda raw: raw.update(observations=[
                {"id": f"negative-{index}", "observed_improvement_bps": -10}
                for index in range(1, 9)
            ])
        )
        try:
            report = solve(load_problem(path))
            self.assertFalse(report["anytime_evidence"]["crossed_threshold"])
            self.assertEqual(report["authority"]["decision"], "recommend")
        finally:
            temporary.cleanup()

    def test_out_of_bound_observation_is_rejected(self) -> None:
        temporary, path = self._counterfactual(
            lambda raw: raw["observations"][0].update(
                observed_improvement_bps=11
            )
        )
        try:
            with self.assertRaisesRegex(ValidationError, "exceeds"):
                load_problem(path)
        finally:
            temporary.cleanup()

    def test_invalid_mixture_weights_are_rejected(self) -> None:
        temporary, path = self._counterfactual(
            lambda raw: raw["components"][0]["mixture_weight"].update(
                numerator=2
            )
        )
        try:
            with self.assertRaisesRegex(ValidationError, "sum to one"):
                load_problem(path)
        finally:
            temporary.cleanup()

    def test_model_shift_revokes(self) -> None:
        temporary, path = self._counterfactual(
            lambda raw: raw.update(model_shift=True)
        )
        try:
            report = solve(load_problem(path))
            self.assertEqual(report["authority"]["decision"], "revoked")
            self.assertEqual(report["authority"]["capital_cap"], 0)
        finally:
            temporary.cleanup()

    def test_statistical_boundary_is_explicit(self) -> None:
        assurance = self.report["assurance"]
        self.assertTrue(assurance["conditional_null_mean_assumed"])
        self.assertTrue(
            assurance["optional_stopping_claim_conditional_on_e_validity"]
        )
        self.assertTrue(
            assurance["measure_theoretic_ville_proof_not_formalized_in_lean"]
        )

    def test_tampered_report_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["authority"]["capital_cap"] = 100
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.problem, tampered)

    def test_solver_is_deterministic(self) -> None:
        self.assertEqual(self.report, solve(self.problem))


if __name__ == "__main__":
    unittest.main()
