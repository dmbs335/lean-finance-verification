from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tools.symbolic_evidence.epistemic_liquidation import (
    LiquidationValidationError,
    load_scenario,
    simulate,
    verify,
)

ROOT = Path(__file__).resolve().parents[3]
SCENARIO = (
    ROOT
    / "examples"
    / "epistemic_liquidation"
    / "shared_vendor_shock.json"
)


class EpistemicLiquidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scenario = load_scenario(SCENARIO)
        self.report = simulate(self.scenario)
        self.shocks = {shock["id"]: shock for shock in self.report["shocks"]}

    def test_low_return_correlation_can_hide_high_evidence_overlap(self) -> None:
        pair = next(
            pair
            for pair in self.report["pair_profiles"]
            if {pair["left"], pair["right"]}
            == {"momentumAlpha", "valueAlpha"}
        )
        self.assertEqual(pair["return_correlation_bps"], 300)
        self.assertGreater(pair["evidence_overlap_bps"], 0)
        self.assertTrue(pair["hidden_epistemic_crowding"])

    def test_shared_vendor_shock_liquidates_both_low_correlation_strategies(self) -> None:
        shock = self.shocks["vendorARevisionFailure"]
        liquidations = {
            response["strategy"]: response["liquidation"]
            for response in shock["strategy_responses"]
        }
        self.assertGreater(liquidations["momentumAlpha"], 0)
        self.assertGreater(liquidations["valueAlpha"], 0)
        self.assertEqual(liquidations["defensiveBeta"], 0)
        self.assertIn(
            {"left": "momentumAlpha", "right": "valueAlpha"},
            shock["synchronized_hidden_pairs"],
        )

    def test_independent_vendor_shock_does_not_hit_shared_vendor_pair(self) -> None:
        shock = self.shocks["independentVendorFailure"]
        liquidations = {
            response["strategy"]: response["liquidation"]
            for response in shock["strategy_responses"]
        }
        self.assertEqual(liquidations["momentumAlpha"], 0)
        self.assertEqual(liquidations["valueAlpha"], 0)
        self.assertGreater(liquidations["defensiveBeta"], 0)
        self.assertEqual(shock["synchronized_hidden_pairs"], [])

    def test_liquidation_generates_nonpositive_asset_impact(self) -> None:
        shock = self.shocks["vendorARevisionFailure"]
        self.assertGreater(shock["total_liquidation"], 0)
        self.assertTrue(all(
            impact <= 0 for impact in shock["price_impact_bps"].values()
        ))
        self.assertTrue(any(
            impact < 0 for impact in shock["price_impact_bps"].values()
        ))

    def test_tampered_report_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["shocks"][0]["total_liquidation"] = 0
        with self.assertRaisesRegex(
            LiquidationValidationError, "exact recomputation"
        ):
            verify(self.scenario, tampered)

    def test_simulation_is_deterministic(self) -> None:
        self.assertEqual(self.report, simulate(self.scenario))


if __name__ == "__main__":
    unittest.main()
