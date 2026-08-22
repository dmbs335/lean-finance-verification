from __future__ import annotations

from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .model import Study

REPORT_SCHEMA = "lfv-pit-micro-study-report-v1"


def _validate_revision_chain(study: Study) -> list[dict[str, Any]]:
    by_id = study.vintage_by_id
    edges: list[dict[str, Any]] = []
    for newer in study.vintages:
        if newer.supersedes is None:
            continue
        older = by_id[newer.supersedes]
        if not (
            older.revision < newer.revision
            and older.first_published_at < newer.first_published_at
        ):
            raise ValidationError("dataset revision chain is non-monotone")
        edges.append({"older": older.id, "newer": newer.id})
    return edges


def _validate_snapshots(study: Study) -> dict[int, tuple[str, ...]]:
    result: dict[int, tuple[str, ...]] = {}
    for snapshot in study.snapshots:
        expected = tuple(sorted(
            asset.id for asset in study.assets if asset.eligible(snapshot.as_of)
        ))
        actual = tuple(sorted(snapshot.members))
        if len(set(snapshot.members)) != len(snapshot.members):
            raise ValidationError(f"universe {snapshot.as_of}: duplicate member")
        if actual != expected:
            raise ValidationError(
                f"universe {snapshot.as_of}: expected {expected}, got {actual}"
            )
        result[snapshot.as_of] = actual
    return result


def _validate_adjustments(study: Study) -> list[dict[str, Any]]:
    by_id = {action.id: action for action in study.actions}
    records: list[dict[str, Any]] = []
    for adjustment in study.adjustments:
        for action_id in adjustment.actions:
            if action_id not in by_id:
                raise ValidationError(f"adjustment {adjustment.id}: unknown action")
            action = by_id[action_id]
            if action.announced_at > adjustment.generated_at:
                raise ValidationError(
                    f"adjustment {adjustment.id}: action was not yet announced"
                )
        records.append({
            "adjustment": adjustment.id,
            "generated_at": adjustment.generated_at,
            "actions": list(adjustment.actions),
        })
    return records


def _price_index(study: Study) -> dict[tuple[str, int, str], Any]:
    result = {}
    for price in study.prices:
        key = (price.asset, price.time, price.vintage)
        if key in result:
            raise ValidationError(f"duplicate price observation {key}")
        result[key] = price
    return result


def check(study: Study) -> dict[str, Any]:
    revision_edges = _validate_revision_chain(study)
    snapshots = _validate_snapshots(study)
    adjustments = _validate_adjustments(study)
    prices = _price_index(study)
    if not study.decisions:
        raise ValidationError("study has no decisions")
    if study.evaluation.registered_at > min(
        decision.decision_at for decision in study.decisions
    ):
        raise ValidationError("evaluation contract was registered after research began")

    decisions: list[dict[str, Any]] = []
    for decision in study.decisions:
        vintage = study.vintage_by_id.get(decision.vintage)
        if vintage is None:
            raise ValidationError("decision references unknown vintage")
        if vintage.first_published_at > decision.decision_at:
            raise ValidationError(
                f"decision {decision.decision_at}: future dataset vintage"
            )
        if decision.as_of not in snapshots:
            raise ValidationError(
                f"decision {decision.decision_at}: missing exact universe snapshot"
            )
        scored: list[dict[str, Any]] = []
        for asset_id in snapshots[decision.as_of]:
            older = prices.get((asset_id, decision.lookback_time, decision.vintage))
            newer = prices.get((asset_id, decision.observation_time, decision.vintage))
            if older is None or newer is None:
                continue
            if older.available_at > decision.decision_at or newer.available_at > decision.decision_at:
                raise ValidationError(
                    f"decision {decision.decision_at}: future price availability"
                )
            score_bps = ((newer.value - older.value) * 10000) // older.value
            scored.append({"asset": asset_id, "score_bps": score_bps})
        if not scored:
            raise ValidationError(f"decision {decision.decision_at}: no scored assets")
        scored.sort(key=lambda item: (-item["score_bps"], item["asset"]))
        decisions.append({
            "decision_at": decision.decision_at,
            "as_of": decision.as_of,
            "vintage": decision.vintage,
            "eligible_assets": list(snapshots[decision.as_of]),
            "scored_assets": scored,
            "selected": scored[0]["asset"],
            "selected_score_bps": scored[0]["score_bps"],
        })

    report = {
        "schema_version": REPORT_SCHEMA,
        "name": study.name,
        "revision_chain": revision_edges,
        "universe_snapshots": [
            {"as_of": as_of, "members": list(members)}
            for as_of, members in sorted(snapshots.items())
        ],
        "adjustment_lineage": adjustments,
        "evaluation_contract": {
            "registered_at": study.evaluation.registered_at,
            "benchmark": study.evaluation.benchmark,
            "metric": study.evaluation.metric,
            "lookback_periods": study.evaluation.lookback_periods,
            "cost_bps": study.evaluation.cost_bps,
        },
        "decisions": decisions,
        "checks": {
            "exact_vintages": True,
            "exact_universes": True,
            "delisted_assets_preserved_before_delisting": True,
            "corporate_actions_known_at_generation": True,
            "evaluation_preregistered": True,
        },
    }
    report["report_sha256"] = __import__("hashlib").sha256(
        canonical_bytes(report)
    ).hexdigest()
    return report


def verify(study: Study, report: Any) -> dict[str, Any]:
    expected = check(study)
    if report != expected:
        raise ValidationError("PIT study report does not match exact recomputation")
    return expected
