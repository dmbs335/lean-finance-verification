from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.autonomous_control.errors import ValidationError
from tools.autonomous_control.model import load_problem
from tools.autonomous_control.solver import solve, verify

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "examples" / "autonomous_control" / "closed_loop.json"


class AutonomousControlFoundationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = load_problem(MODEL)
        self.report = solve(self.problem)
        self.by_state = {
            row["state"]: row for row in self.report["states"]
        }

    def test_two_step_viability_excludes_terminal_ruin(self) -> None:
        self.assertEqual(
            self.report["viability_layers"],
            [
                ["margin", "normal", "stressed"],
                ["margin", "normal", "stressed"],
                ["margin", "normal", "stressed"],
            ],
        )

    def test_shield_replaces_known_unsafe_proposals(self) -> None:
        self.assertEqual(
            self.by_state["normal"]["shielded_action"], "increase"
        )
        self.assertEqual(
            self.by_state["stressed"]["shielded_action"], "reduce"
        )
        self.assertEqual(
            self.by_state["margin"]["shielded_action"], "reduce"
        )
        self.assertTrue(
            self.report["controlled_claims"][
                "shield_never_emits_known_unsafe_action"
            ]
        )

    def test_candidate_is_supported_safe_and_baseline_constrained(self) -> None:
        self.assertEqual(
            self.report["candidate_policy"],
            {
                "normal": "increase",
                "stressed": "reduce",
                "margin": "reduce",
                "ruin": "hold",
            },
        )
        certificate = self.report["policy_certificate"]
        self.assertTrue(certificate["all_candidate_actions_safe"])
        self.assertTrue(certificate["respects_baseline_outside_support"])

    def test_pessimistic_policy_improvement_clears_margin(self) -> None:
        certificate = self.report["policy_certificate"]
        self.assertEqual(certificate["baseline_score_lcb"], 2)
        self.assertEqual(certificate["candidate_score_lcb"], 8)
        self.assertEqual(certificate["improvement_lcb"], 6)
        self.assertTrue(certificate["improvement_passed"])

    def test_authority_advances_only_one_level(self) -> None:
        authority = self.report["authority"]
        self.assertEqual(authority["current"], "recommend")
        self.assertEqual(authority["decision"], "microAutonomy")
        self.assertEqual(authority["capital_cap"], 10)
        self.assertTrue(
            self.report["controlled_claims"][
                "authority_advances_at_most_one_level"
            ]
        )

    def test_breach_counterfactual_revokes_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "model.json"
            raw = json.loads(MODEL.read_text(encoding="utf-8"))
            raw["authority"]["operational_breach"] = True
            path.write_text(json.dumps(raw), encoding="utf-8")
            report = solve(load_problem(path))
            self.assertEqual(report["authority"]["decision"], "revoked")
            self.assertEqual(report["authority"]["capital_cap"], 0)

    def test_unsafe_baseline_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "model.json"
            raw = json.loads(MODEL.read_text(encoding="utf-8"))
            state = next(item for item in raw["states"] if item["id"] == "margin")
            state["baseline_action"] = "hold"
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "baseline policy"):
                solve(load_problem(path))

    def test_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["authority"]["capital_cap"] = 100
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.problem, tampered)

    def test_solver_is_deterministic(self) -> None:
        self.assertEqual(self.report, solve(self.problem))


if __name__ == "__main__":
    unittest.main()
