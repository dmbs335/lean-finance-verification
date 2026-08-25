from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.belief_control.errors import ValidationError
from tools.belief_control.model import load_problem
from tools.belief_control.solver import solve, verify

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "examples" / "belief_control" / "hidden_regime.json"


class BeliefStateRobustControlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = load_problem(MODEL)
        self.report = solve(self.problem)
        self.by_observation = {
            row["observation"]: row for row in self.report["observations"]
        }

    def test_prior_robust_action_is_hold(self) -> None:
        selected = self.report["prior"]["control"]["selected"]
        self.assertEqual(selected["action"], "hold")
        self.assertEqual(selected["robust_net_value_bps"], 1)

    def test_stable_observation_removes_bear_and_selects_increase(self) -> None:
        stable = self.by_observation["stable"]
        self.assertEqual(stable["posterior_unnormalized"], {
            "bull": 8, "base": 10, "bear": 0,
        })
        self.assertEqual(stable["posterior_support"], ["bull", "base"])
        self.assertEqual(stable["control"]["selected"]["action"], "increase")
        self.assertEqual(
            stable["control"]["selected"]["robust_net_value_bps"], 5
        )

    def test_stress_observation_removes_bull_and_selects_reduce(self) -> None:
        stress = self.by_observation["stress"]
        self.assertEqual(stress["posterior_unnormalized"], {
            "bull": 0, "base": 5, "bear": 12,
        })
        self.assertEqual(stress["posterior_support"], ["base", "bear"])
        self.assertEqual(stress["control"]["selected"]["action"], "reduce")
        self.assertEqual(
            stress["control"]["selected"]["robust_net_value_bps"], 3
        )

    def test_posterior_probabilities_are_exact(self) -> None:
        stable = self.by_observation["stable"]["posterior_probability"]
        self.assertEqual(stable["bull"], {"numerator": 4, "denominator": 9})
        self.assertEqual(stable["base"], {"numerator": 5, "denominator": 9})
        stress = self.by_observation["stress"]["posterior_probability"]
        self.assertEqual(stress["bear"], {"numerator": 12, "denominator": 17})

    def test_query_has_positive_worst_case_value(self) -> None:
        query = self.report["query"]
        self.assertEqual(query["worst_post_observation_value_bps"], 3)
        self.assertEqual(query["net_post_query_value_bps"], 2)
        self.assertEqual(query["robust_value_of_information_bps"], 1)
        self.assertEqual(query["decision"], "acquireEvidence")

    def test_zero_mass_observation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "model.json"
            raw = json.loads(MODEL.read_text(encoding="utf-8"))
            raw["observations"][0]["likelihood_weights"] = {
                hidden: 0 for hidden in raw["prior_weights"]
            }
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "zero posterior"):
                load_problem(path)

    def test_tampered_report_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["query"]["decision"] = "actNow"
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.problem, tampered)

    def test_solver_is_deterministic(self) -> None:
        self.assertEqual(self.report, solve(self.problem))


if __name__ == "__main__":
    unittest.main()
