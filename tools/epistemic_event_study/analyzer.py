from __future__ import annotations

import hashlib
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .model import MatchedPair, Plan, StrategyWindow

REPORT_SCHEMA = "lfv-epistemic-event-study-report-v1"


def _pre_change(window: StrategyWindow) -> int:
    return window.pre_event_outflow_bps - window.baseline_outflow_bps


def _event_change(window: StrategyWindow) -> int:
    return window.post_event_outflow_bps - window.pre_event_outflow_bps


def _pair_result(plan: Plan, pair: MatchedPair) -> dict[str, Any]:
    treated_exposed = plan.failed_domain in pair.treated.evidence_domains
    control_unexposed = plan.failed_domain not in pair.control.evidence_domains
    maximum_distance = max(pair.conventional_distance_bps.values())
    matching_passed = (
        treated_exposed
        and control_unexposed
        and maximum_distance <= plan.maximum_match_distance_bps
    )
    treated_pre = _pre_change(pair.treated)
    control_pre = _pre_change(pair.control)
    pretrend_did = treated_pre - control_pre
    pretrend_passed = (
        abs(pretrend_did) <= plan.maximum_absolute_pretrend_did_bps
    )
    treated_event = _event_change(pair.treated)
    control_event = _event_change(pair.control)
    event_did = treated_event - control_event
    return {
        "pair": pair.id,
        "treated": pair.treated.id,
        "control": pair.control.id,
        "failed_domain": plan.failed_domain,
        "treated_exposed": treated_exposed,
        "control_unexposed": control_unexposed,
        "conventional_distance_bps": dict(pair.conventional_distance_bps),
        "maximum_distance_bps": maximum_distance,
        "matching_passed": matching_passed,
        "pretrend": {
            "treated_change_bps": treated_pre,
            "control_change_bps": control_pre,
            "did_bps": pretrend_did,
            "passed": pretrend_passed,
        },
        "event": {
            "treated_change_bps": treated_event,
            "control_change_bps": control_event,
            "did_bps": event_did,
        },
    }


def analyze(plan: Plan) -> dict[str, Any]:
    pair_results = [_pair_result(plan, pair) for pair in plan.pairs]
    preregistration_passed = plan.preregistered_at < plan.event_time
    matching_passed = all(pair["matching_passed"] for pair in pair_results)
    pretrend_passed = all(pair["pretrend"]["passed"] for pair in pair_results)
    event_did_numerator = sum(
        pair["event"]["did_bps"] for pair in pair_results
    )
    event_did_denominator = len(pair_results)
    event_effect_passed = (
        event_did_numerator
        >= plan.minimum_average_event_did_bps * event_did_denominator
    )
    all_pass = (
        preregistration_passed
        and matching_passed
        and pretrend_passed
        and event_effect_passed
    )
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": plan.name,
        "plan_sha256": plan.digest,
        "failed_domain": plan.failed_domain,
        "preregistered_at": plan.preregistered_at,
        "event_time": plan.event_time,
        "status": "accepted-controlled" if all_pass else "rejected",
        "gates": {
            "preregistration": {
                "passed": preregistration_passed,
                "strictly_before_event": preregistration_passed,
            },
            "matching": {
                "passed": matching_passed,
                "maximum_allowed_distance_bps": (
                    plan.maximum_match_distance_bps
                ),
            },
            "pretrend": {
                "passed": pretrend_passed,
                "maximum_absolute_did_bps": (
                    plan.maximum_absolute_pretrend_did_bps
                ),
            },
            "event_effect": {
                "passed": event_effect_passed,
                "minimum_average_did_bps": (
                    plan.minimum_average_event_did_bps
                ),
                "did_numerator_bps": event_did_numerator,
                "did_denominator": event_did_denominator,
                "average_did_bps_floor": (
                    event_did_numerator // event_did_denominator
                ),
            },
        },
        "pairs": pair_results,
        "certificate": (
            {
                "plan_sha256": plan.digest,
                "failed_domain": plan.failed_domain,
                "pair_count": event_did_denominator,
                "event_did_numerator_bps": event_did_numerator,
                "event_did_denominator": event_did_denominator,
                "residual_boundaries": [
                    "controlled synthetic withdrawals",
                    "declared matching dimensions and tolerances",
                    "no inference of real-market causality",
                ],
            }
            if all_pass
            else None
        ),
    }
    report["report_sha256"] = hashlib.sha256(
        canonical_bytes(report)
    ).hexdigest()
    return report


def verify(plan: Plan, report: Any) -> dict[str, Any]:
    expected = analyze(plan)
    if report != expected:
        raise ValidationError(
            "epistemic event-study report does not match exact recomputation"
        )
    return expected
