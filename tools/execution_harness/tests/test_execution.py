from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.execution_harness.errors import ValidationError
from tools.execution_harness.model import load_problem
from tools.execution_harness.solver import solve, verify

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "examples" / "execution_harness" / "controlled_buy.json"


class ProofCarryingExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = load_problem(MODEL)
        self.report = solve(self.problem)

    def _counterfactual(self, mutate):
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / "model.json"
        raw = json.loads(MODEL.read_text(encoding="utf-8"))
        mutate(raw)
        path.write_text(json.dumps(raw), encoding="utf-8")
        return temporary, load_problem(path)

    def test_controlled_order_reconciles_exactly(self) -> None:
        recon = self.report["reconciliation"]
        self.assertEqual(recon["filled_qty"], 100)
        self.assertEqual(recon["remaining_authorized_qty"], 0)
        self.assertEqual(recon["cash_delta"], -1002)
        self.assertEqual(recon["final_cash"], 8998)
        self.assertEqual(recon["inventory_delta"], 100)
        self.assertEqual(recon["final_inventory"], 100)

    def test_lifecycle_is_ordered_and_reconciled(self) -> None:
        lifecycle = self.report["lifecycle"]
        self.assertTrue(lifecycle["valid"])
        self.assertEqual(lifecycle["states"][0], "proposed")
        self.assertEqual(lifecycle["states"][-1], "reconciled")
        self.assertEqual(
            lifecycle["terminal_before_reconciliation"], "filled"
        )

    def test_revoked_authority_cannot_submit(self) -> None:
        temporary, problem = self._counterfactual(
            lambda raw: raw["order"].update(authority="revoked")
        )
        try:
            with self.assertRaisesRegex(ValidationError, "cannot submit"):
                solve(problem)
        finally:
            temporary.cleanup()

    def test_overfill_is_rejected(self) -> None:
        temporary, problem = self._counterfactual(
            lambda raw: raw["fills"][1].update(qty=61)
        )
        try:
            with self.assertRaisesRegex(ValidationError, "exceed"):
                solve(problem)
        finally:
            temporary.cleanup()

    def test_duplicate_fill_id_is_rejected(self) -> None:
        temporary, problem = self._counterfactual(
            lambda raw: raw["fills"][1].update(id="fill-1")
        )
        try:
            with self.assertRaisesRegex(ValidationError, "duplicate"):
                solve(problem)
        finally:
            temporary.cleanup()

    def test_illegal_transition_is_rejected(self) -> None:
        temporary, problem = self._counterfactual(
            lambda raw: raw["lifecycle"].__setitem__(2, "submitted")
        )
        try:
            with self.assertRaisesRegex(ValidationError, "illegal"):
                solve(problem)
        finally:
            temporary.cleanup()

    def test_limit_price_violation_is_rejected(self) -> None:
        temporary, problem = self._counterfactual(
            lambda raw: raw["fills"][0].update(price=11)
        )
        try:
            with self.assertRaisesRegex(ValidationError, "limit price"):
                solve(problem)
        finally:
            temporary.cleanup()

    def test_tampered_report_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["reconciliation"]["final_cash"] = 10000
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.problem, tampered)

    def test_solver_is_deterministic(self) -> None:
        self.assertEqual(self.report, solve(self.problem))


if __name__ == "__main__":
    unittest.main()
