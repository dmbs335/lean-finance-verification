from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from tools.model_family_synth.errors import ValidationError
from tools.model_family_synth.model import load_problem
from tools.model_family_synth.solver import solve, verify

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "examples" / "model_family" / "guard_ambiguity.json"


class ModelFamilySynthesisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = load_problem(MODEL)
        self.report = solve(self.problem)

    def test_point_model_underestimates_family_evidence(self) -> None:
        self.assertEqual(
            self.report["point_optimum"]["selected"]["channels"],
            ["publication"],
        )
        self.assertEqual(
            self.report["family_optimum"]["selected"]["channels"],
            ["publication", "mutationReceipt"],
        )
        self.assertEqual(self.report["underestimation_gap"], 3)

    def test_cross_model_counterexample_is_reported(self) -> None:
        pairs = {
            (edge["left"], edge["right"])
            for edge in self.report["cross_model_disagreement_edges"]
        }
        self.assertIn(("narrowHonest", "permissiveSilentMutation"), pairs)

    def test_family_lower_cost_candidate_has_counterexample(self) -> None:
        publication = next(
            candidate
            for candidate in self.report["family_optimum"]["lower_cost_failures"]
            if candidate["channels"] == ["publication"]
        )
        self.assertFalse(publication["verifies"])
        self.assertEqual(
            set(publication["uncovered"]["separators"]),
            {"mutationReceipt"},
        )

    def test_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["underestimation_gap"] = 0
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.problem, tampered)

    def test_solver_is_deterministic(self) -> None:
        self.assertEqual(self.report, solve(self.problem))


if __name__ == "__main__":
    unittest.main()
