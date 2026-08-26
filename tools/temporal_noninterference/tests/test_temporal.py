from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tools.temporal_noninterference.audit import audit, verify
from tools.temporal_noninterference.errors import ValidationError
from tools.temporal_noninterference.model import load_problem

ROOT = Path(__file__).resolve().parents[3]
MODEL = (
    ROOT
    / "examples"
    / "temporal_noninterference"
    / "gs_quant_style.json"
)


class TemporalNoninterferenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = load_problem(MODEL)
        self.report = audit(self.problem)
        self.by_id = {
            item["engine"]: item
            for item in self.report["engine_audits"]
        }

    def test_only_causal_forward_fill_passes_all_contracts(self) -> None:
        self.assertEqual(
            self.report["aggregate"]["safe_engines"],
            ["causalForwardFill"],
        )
        causal = self.by_id["causalForwardFill"]
        self.assertTrue(causal["summary"]["contract_passes"])
        self.assertEqual(
            causal["summary"]["temporal_noninterference_violation_count"],
            0,
        )
        self.assertEqual(
            causal["summary"]["availability_violation_count"], 0
        )
        self.assertFalse(
            causal["summary"]["source_mutation_observed"]
        )

    def test_future_append_changes_global_last_fill_past_output(self) -> None:
        engine = self.by_id["globalLastFill"]
        mutation = next(
            item for item in engine["mutations"]
            if item["mutation"] == "appendTwoFutureExtremes"
        )
        self.assertTrue(
            mutation["causal_prefix_equivalent_through_cutoff"]
        )
        self.assertTrue(
            mutation["temporal_noninterference_violation"]
        )
        self.assertEqual(
            mutation["first_divergence"]["decision_time"], 35
        )
        self.assertEqual(
            mutation["minimal_violation_witness"]["operation_indexes"],
            [0],
        )
        self.assertEqual(
            mutation["first_divergence"]["baseline"][
                "selected_point_ids"
            ],
            ["p3"],
        )
        self.assertEqual(
            mutation["first_divergence"]["mutated"][
                "selected_point_ids"
            ],
            ["p6"],
        )

    def test_future_revision_changes_bidirectional_interpolation(self) -> None:
        engine = self.by_id["bidirectionalInterpolation"]
        mutation = next(
            item for item in engine["mutations"]
            if item["mutation"] == "reviseFutureValue"
        )
        self.assertTrue(
            mutation["causal_prefix_equivalent_through_cutoff"]
        )
        self.assertTrue(
            mutation["temporal_noninterference_violation"]
        )
        self.assertEqual(
            mutation["distance"]["mark_l1"],
            {"numerator": 338, "denominator": 1},
        )
        self.assertEqual(
            mutation["distance"]["position_l1"], 2
        )

    def test_observation_time_alone_is_not_availability(self) -> None:
        engine = self.by_id["observationOnlyForwardFill"]
        violations = engine["baseline"]["availability_violations"]
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["point_id"], "p2")
        self.assertEqual(
            violations[0]["reasons"], ["available_after_decision"]
        )
        self.assertEqual(
            engine["summary"][
                "temporal_noninterference_violation_count"
            ],
            0,
        )
        self.assertFalse(engine["summary"]["contract_passes"])

    def test_mutating_engine_is_rejected_even_if_outputs_replay(self) -> None:
        engine = self.by_id["mutatingGlobalLastFill"]
        self.assertTrue(engine["baseline"]["source_mutated"])
        self.assertEqual(
            engine["baseline"]["source_order"],
            ["p0", "p4", "p1", "p2", "p3"],
        )
        self.assertEqual(
            engine["baseline"]["final_source_order"],
            ["p0", "p1", "p2", "p3", "p4"],
        )
        self.assertTrue(
            engine["summary"]["source_mutation_observed"]
        )
        self.assertFalse(engine["summary"]["contract_passes"])

    def test_representation_only_changes_preserve_every_output(self) -> None:
        for engine in self.report["engine_audits"]:
            mutation = next(
                item for item in engine["mutations"]
                if item["mutation"] == "representationEquivalent"
            )
            self.assertTrue(
                mutation["causal_prefix_equivalent_through_cutoff"]
            )
            self.assertTrue(
                mutation["outputs_equal_through_cutoff"]
            )
            self.assertFalse(
                mutation["temporal_noninterference_violation"]
            )

    def test_changed_past_information_does_not_trigger_false_positive(self) -> None:
        causal = self.by_id["causalForwardFill"]
        mutation = next(
            item for item in causal["mutations"]
            if item["mutation"] == "reviseKnownPast"
        )
        self.assertFalse(
            mutation["causal_prefix_equivalent_through_cutoff"]
        )
        self.assertFalse(
            mutation["temporal_noninterference_violation"]
        )
        self.assertFalse(mutation["outputs_equal_through_cutoff"])

    def test_report_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["aggregate"]["safe_engines"] = []
        with self.assertRaisesRegex(
            ValidationError, "exact recomputation"
        ):
            verify(self.problem, tampered)

    def test_audit_is_deterministic(self) -> None:
        self.assertEqual(self.report, audit(self.problem))


if __name__ == "__main__":
    unittest.main()
