from __future__ import annotations

import copy
import unittest
from dataclasses import replace
from pathlib import Path

from tools.symbolic_evidence.certifiability_crowding import (
    CertifiabilityCrowdingValidationError,
    Scenario,
    load_scenario,
    simulate,
    verify,
)

ROOT = Path(__file__).resolve().parents[3]
SCENARIO = (
    ROOT
    / "examples"
    / "certifiability_crowding"
    / "lifecycle.json"
)


class CertifiabilityCrowdingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scenario = load_scenario(SCENARIO)
        self.report = simulate(self.scenario)
        self.by_id = {
            strategy["id"]: strategy
            for strategy in self.report["strategies"]
        }

    def test_all_evidence_upgrades_create_the_declared_crowding_chain(self) -> None:
        self.assertEqual(self.report["certifiability_crowding_count"], 3)
        for strategy in self.report["strategies"]:
            self.assertTrue(strategy["certifiability_increased"])
            self.assertTrue(strategy["capital_increased"])
            self.assertTrue(strategy["impact_increased"])
            self.assertTrue(strategy["deployable_alpha_decreased"])

    def test_scalable_strategy_survives_the_capital_inflow(self) -> None:
        strategy = self.by_id["scalableSignal"]
        self.assertEqual(strategy["before"]["deployable_alpha_bps"], 50)
        self.assertEqual(strategy["after"]["deployable_alpha_bps"], 48)
        self.assertTrue(strategy["after"]["investable"])
        self.assertFalse(strategy["capacity_death"])

    def test_capacity_constrained_strategies_lose_deployability(self) -> None:
        self.assertEqual(self.report["capacity_death_count"], 2)
        constrained = self.by_id["capacityConstrainedAlpha"]
        self.assertLessEqual(constrained["after"]["deployable_alpha_bps"], 0)
        self.assertTrue(constrained["capacity_death"])

    def test_more_capacity_reduces_the_crowding_damage(self) -> None:
        constrained = self.scenario.strategies[1]
        expanded = replace(constrained, id="expandedCapacity", capacity=10_000)
        expanded_report = simulate(
            Scenario(
                source=self.scenario.source,
                name="expanded-capacity-counterfactual",
                strategies=(expanded,),
            )
        )["strategies"][0]
        self.assertGreater(
            expanded_report["after"]["deployable_alpha_bps"],
            self.by_id["capacityConstrainedAlpha"]["after"][
                "deployable_alpha_bps"
            ],
        )
        self.assertFalse(expanded_report["capacity_death"])

    def test_no_evidence_upgrade_produces_no_certifiability_chain(self) -> None:
        baseline = replace(
            self.scenario.strategies[0],
            id="noUpgrade",
            evidence_upgrade_bps=0,
        )
        result = simulate(
            Scenario(
                source=self.scenario.source,
                name="no-upgrade-counterfactual",
                strategies=(baseline,),
            )
        )["strategies"][0]
        self.assertFalse(result["certifiability_increased"])
        self.assertFalse(result["capital_increased"])
        self.assertFalse(result["impact_increased"])
        self.assertFalse(result["certifiability_crowding_chain"])

    def test_tampered_report_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["capacity_death_count"] = 0
        with self.assertRaisesRegex(
            CertifiabilityCrowdingValidationError,
            "exact recomputation",
        ):
            verify(self.scenario, tampered)

    def test_simulation_is_deterministic(self) -> None:
        self.assertEqual(self.report, simulate(self.scenario))


if __name__ == "__main__":
    unittest.main()
