from __future__ import annotations

import copy
import subprocess
import unittest
from pathlib import Path

from tools.evidence_synth.canonical import canonical_bytes
from tools.evidence_synth.errors import ValidationError
from tools.semantics_version_space.model import load_model
from tools.semantics_version_space.solver import solve_model, verify_report

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = (
    REPOSITORY_ROOT
    / "examples"
    / "semantics_version_space"
    / "cost_model_tampering.json"
)
LEAN_PATH = (
    REPOSITORY_ROOT
    / "LeanFinance"
    / "Generated"
    / "CostModelSemanticsVersionSpace.lean"
)


class SemanticsVersionSpaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = load_model(MODEL_PATH)
        self.report = solve_model(self.model)

    def test_two_guard_hypotheses_remain_consistent(self) -> None:
        self.assertEqual(self.report["candidate_literal_count"], 3)
        self.assertEqual(self.report["candidate_guard_count"], 8)
        self.assertEqual(self.report["consistent_hypothesis_count"], 2)
        guards = [
            {
                (literal["variable"], literal["value"])
                for literal in hypothesis["guard"]
            }
            for hypothesis in self.report["hypotheses"]
        ]
        required = {
            ("baselineExecuted", True),
            ("resultPublished", False),
        }
        self.assertTrue(all(required.issubset(guard) for guard in guards))
        self.assertEqual(
            sum(("costModelTampered", False) in guard for guard in guards),
            1,
        )

    def test_best_probe_is_the_unique_ambiguous_state(self) -> None:
        probe = self.report["best_probe"]
        self.assertEqual(
            probe["state"],
            {
                "baselineExecuted": True,
                "resultPublished": False,
                "costModelTampered": True,
            },
        )
        self.assertEqual(probe["group_count"], 2)
        self.assertEqual(probe["largest_remaining_group"], 1)
        self.assertEqual(probe["cost"], 2)
        self.assertEqual(self.report["distinguishing_probe_count"], 1)

    def test_report_is_deterministic_and_tamper_evident(self) -> None:
        second = solve_model(self.model)
        self.assertEqual(canonical_bytes(self.report), canonical_bytes(second))
        tampered = copy.deepcopy(self.report)
        tampered["consistent_hypothesis_count"] = 1
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify_report(self.model, tampered)

    def test_generated_lean_witness_typechecks(self) -> None:
        result = subprocess.run(
            ["lake", "env", "lean", str(LEAN_PATH.relative_to(REPOSITORY_ROOT))],
            cwd=REPOSITORY_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=180,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg="generated version-space Lean failed:\n" + result.stdout,
        )


if __name__ == "__main__":
    unittest.main()
