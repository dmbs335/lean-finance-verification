from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.epistemic_liquidation.errors import ValidationError
from tools.epistemic_liquidation.model import load_scenario
from tools.epistemic_liquidation.simulator import simulate, verify

ROOT = Path(__file__).resolve().parents[3]
SCENARIO = ROOT / "examples" / "epistemic_liquidation" / "shared_vendor_shock.json"


class EpistemicLiquidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scenario = load_scenario(SCENARIO)
        self.report = simulate(self.scenario)

    def _mutated(self, mutate):
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / "scenario.json"
        raw = json.loads(SCENARIO.read_text(encoding="utf-8"))
        mutate(raw)
        path.write_text(json.dumps(raw), encoding="utf-8")
        return temporary, load_scenario(path)

    def test_low_return_correlation_pair_has_hidden_common_risk(self) -> None:
        hidden = [pair for pair in self.report["pairs"] if pair["hidden_common_risk"]]
        self.assertEqual(len(hidden), 1)
        self.assertEqual(
            {hidden[0]["left"], hidden[0]["right"]},
            {"globalValue", "usMomentum"},
        )
        self.assertEqual(hidden[0]["shared_failed_domains"], ["vendor-a"])

    def test_independent_strategy_avoids_first_round_evidence_withdrawal(self) -> None:
        independent = next(
            row for row in self.report["strategies"]
            if row["strategy"] == "independentTrend"
        )
        self.assertEqual(independent["evidence_withdrawal_units"], 0)
        self.assertEqual(independent["failed_domains"], [])

    def test_market_feedback_amplifies_the_initial_evidence_shock(self) -> None:
        aggregate = self.report["aggregate"]
        self.assertGreater(aggregate["evidence_withdrawal_units"], 0)
        self.assertGreater(aggregate["margin_withdrawal_units"], 0)
        self.assertGreater(
            aggregate["total_withdrawal_units"],
            aggregate["evidence_withdrawal_units"],
        )
        self.assertGreaterEqual(
            self.report["final_market_impact_bps"],
            self.report["initial_market_impact_bps"],
        )

    def test_removing_the_shared_vendor_shock_removes_epistemic_origin(self) -> None:
        temporary, scenario = self._mutated(
            lambda raw: raw.update(shocks=[])
        )
        try:
            report = simulate(scenario)
            self.assertEqual(report["aggregate"]["evidence_withdrawal_units"], 0)
            self.assertEqual(report["aggregate"]["hidden_common_risk_pairs"], 0)
            self.assertEqual(report["final_market_impact_bps"], 0)
        finally:
            temporary.cleanup()

    def test_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["aggregate"]["total_withdrawal_units"] = 0
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.scenario, tampered)

    def test_simulation_is_deterministic(self) -> None:
        self.assertEqual(self.report, simulate(self.scenario))


if __name__ == "__main__":
    unittest.main()
