from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tools.certifiability_crowding.errors import ValidationError
from tools.certifiability_crowding.model import load_scenario
from tools.certifiability_crowding.simulator import simulate, verify

ROOT = Path(__file__).resolve().parents[3]
SCENARIO = ROOT / "examples" / "certifiability_crowding" / "capacity.json"


class CertifiabilityCrowdingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scenario = load_scenario(SCENARIO)
        self.report = simulate(self.scenario)

    def test_stronger_evidence_increases_allocation(self) -> None:
        for row in self.report["strategies"]:
            self.assertGreaterEqual(
                row["after"]["allocation_units"],
                row["before"]["allocation_units"],
            )
        self.assertGreater(
            self.report["aggregate"]["allocation_after_units"],
            self.report["aggregate"]["allocation_before_units"],
        )

    def test_positive_impact_strategies_exhibit_the_paradox(self) -> None:
        paradoxes = {
            row["strategy"]
            for row in self.report["strategies"]
            if row["certifiability_crowding_paradox"]
        }
        self.assertEqual(
            paradoxes, {"limitedCapacitySignal", "scalableValue"}
        )
        self.assertEqual(self.report["aggregate"]["paradox_count"], 2)

    def test_limited_capacity_alpha_turns_negative(self) -> None:
        limited = next(
            row for row in self.report["strategies"]
            if row["strategy"] == "limitedCapacitySignal"
        )
        self.assertEqual(limited["before"]["deployable_alpha_bps"], 380)
        self.assertEqual(limited["after"]["deployable_alpha_bps"], -580)
        self.assertEqual(limited["deployable_alpha_change_bps"], -960)
        self.assertEqual(
            self.report["aggregate"][
                "negative_deployable_alpha_after_verification"
            ],
            1,
        )

    def test_limited_capacity_is_capacity_death_not_epistemic_death(self) -> None:
        limited = next(
            row for row in self.report["strategies"]
            if row["strategy"] == "limitedCapacitySignal"
        )
        self.assertTrue(limited["capacity_death_after_verification"])
        self.assertFalse(limited["epistemic_death_after_verification"])
        self.assertEqual(
            limited["alpha_death_modes_after_verification"], ["capacity"]
        )
        self.assertEqual(self.report["aggregate"]["capacity_death_count"], 1)
        self.assertEqual(self.report["aggregate"]["epistemic_death_count"], 0)

    def test_zero_impact_changes_allocation_but_not_alpha(self) -> None:
        benchmark = next(
            row for row in self.report["strategies"]
            if row["strategy"] == "zeroImpactBenchmark"
        )
        self.assertGreater(
            benchmark["after"]["allocation_units"],
            benchmark["before"]["allocation_units"],
        )
        self.assertEqual(benchmark["deployable_alpha_change_bps"], 0)
        self.assertFalse(benchmark["certifiability_crowding_paradox"])
        self.assertEqual(
            benchmark["alpha_death_modes_after_verification"], []
        )

    def test_structural_law_holds_for_every_strategy(self) -> None:
        self.assertTrue(
            self.report["aggregate"]["all_structural_laws_hold"]
        )
        self.assertTrue(all(
            row["structural_law_holds"]
            for row in self.report["strategies"]
        ))

    def test_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["aggregate"]["capacity_death_count"] = 0
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.scenario, tampered)

    def test_simulation_is_deterministic(self) -> None:
        self.assertEqual(self.report, simulate(self.scenario))


if __name__ == "__main__":
    unittest.main()
