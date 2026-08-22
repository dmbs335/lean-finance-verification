from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, product
from typing import Any

from tools.evidence_synth.canonical import (
    CANONICAL_FORMAT,
    canonical_dumps,
    document_digest,
)
from tools.evidence_synth.errors import ValidationError

from .model import VersionSpaceModel

REPORT_SCHEMA = "lfv-action-version-space-report-v1"
REPORT_DIGEST_SCHEMA = "lfv-action-version-space-report-digest-v1"
MODEL_DIGEST_SCHEMA = "lfv-action-version-space-model-digest-v1"


@dataclass(frozen=True)
class Literal:
    variable: str
    value: bool

    def as_dict(self) -> dict[str, Any]:
        return {"variable": self.variable, "value": self.value}


@dataclass(frozen=True)
class Hypothesis:
    id: str
    guard: tuple[Literal, ...]
    effects: tuple[tuple[str, bool], ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "guard": [literal.as_dict() for literal in self.guard],
            "effects": {field: value for field, value in self.effects},
        }


def _guard_holds(guard: tuple[Literal, ...], state: dict[str, bool]) -> bool:
    return all(state[literal.variable] == literal.value for literal in guard)


def _apply(hypothesis: Hypothesis, state: dict[str, bool]) -> dict[str, bool]:
    result = dict(state)
    result.update(dict(hypothesis.effects))
    return result


def _outcome(hypothesis: Hypothesis, state: dict[str, bool]) -> dict[str, Any]:
    if not _guard_holds(hypothesis.guard, state):
        return {"enabled": False}
    return {"enabled": True, "after": _apply(hypothesis, state)}


def _stable_positive_literals(model: VersionSpaceModel) -> tuple[Literal, ...]:
    literals: list[Literal] = []
    for variable in model.variable_ids:
        values = {observation.before[variable] for observation in model.positive}
        if len(values) == 1:
            literals.append(Literal(variable=variable, value=values.pop()))
    return tuple(literals)


def _effect_assignment(model: VersionSpaceModel) -> tuple[tuple[str, bool], ...]:
    result: list[tuple[str, bool]] = []
    for field in model.effect_fields:
        values = {observation.after[field] for observation in model.positive}
        if len(values) != 1:
            raise ValidationError(
                f"positive observations disagree on constant effect field {field!r}"
            )
        result.append((field, values.pop()))
    return tuple(result)


def enumerate_hypotheses(model: VersionSpaceModel) -> tuple[Hypothesis, ...]:
    literals = _stable_positive_literals(model)
    effects = _effect_assignment(model)
    hypotheses: list[Hypothesis] = []
    index = 0
    for size in range(len(literals) + 1):
        for chosen in combinations(literals, size):
            if any(_guard_holds(chosen, state) for state in model.negative):
                continue
            hypothesis = Hypothesis(
                id=f"hypothesis-{index}",
                guard=tuple(chosen),
                effects=effects,
            )
            if not all(
                _guard_holds(hypothesis.guard, observation.before)
                and all(
                    _apply(hypothesis, observation.before)[field]
                    == observation.after[field]
                    for field in model.effect_fields
                )
                for observation in model.positive
            ):
                continue
            hypotheses.append(hypothesis)
            index += 1
    if not hypotheses:
        raise ValidationError(
            "no guard/effect hypothesis is consistent with all observations"
        )
    return tuple(hypotheses)


def _all_states(model: VersionSpaceModel) -> tuple[dict[str, bool], ...]:
    return tuple(
        dict(zip(model.variable_ids, values, strict=True))
        for values in product([False, True], repeat=len(model.variables))
    )


def _probe_cost(model: VersionSpaceModel, state: dict[str, bool]) -> int:
    return sum(
        variable.probe_cost
        for variable in model.variables
        if state[variable.id] != variable.initial
    )


def _partition(
    hypotheses: tuple[Hypothesis, ...], state: dict[str, bool]
) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for hypothesis in hypotheses:
        outcome = _outcome(hypothesis, state)
        key = canonical_dumps(outcome)
        if key not in groups:
            groups[key] = {"outcome": outcome, "hypotheses": []}
        groups[key]["hypotheses"].append(hypothesis.id)
    return list(groups.values())


def rank_probes(
    model: VersionSpaceModel,
    hypotheses: tuple[Hypothesis, ...],
) -> list[dict[str, Any]]:
    probes: list[dict[str, Any]] = []
    for state in _all_states(model):
        partition = _partition(hypotheses, state)
        if len(partition) < 2:
            continue
        largest_group = max(len(group["hypotheses"]) for group in partition)
        probes.append(
            {
                "state": state,
                "cost": _probe_cost(model, state),
                "partition": partition,
                "largest_remaining_group": largest_group,
                "group_count": len(partition),
            }
        )
    probes.sort(
        key=lambda probe: (
            probe["largest_remaining_group"],
            -probe["group_count"],
            probe["cost"],
            tuple(probe["state"][variable] for variable in model.variable_ids),
        )
    )
    return probes


def normalized_model(model: VersionSpaceModel) -> dict[str, Any]:
    return {
        "schema_version": "lfv-action-semantics-version-space-v1",
        "name": model.name,
        "variables": [
            {
                "id": variable.id,
                "initial": variable.initial,
                "probe_cost": variable.probe_cost,
                "description": variable.description,
            }
            for variable in model.variables
        ],
        "effect_fields": list(model.effect_fields),
        "positive_observations": [
            {"before": observation.before, "after": observation.after}
            for observation in model.positive
        ],
        "negative_states": list(model.negative),
    }


def solve_model(model: VersionSpaceModel) -> dict[str, Any]:
    hypotheses = enumerate_hypotheses(model)
    probes = rank_probes(model, hypotheses)
    core: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "canonical_format": CANONICAL_FORMAT,
        "name": model.name,
        "model_digest": document_digest(
            "actionSemanticsVersionSpace",
            MODEL_DIGEST_SCHEMA,
            normalized_model(model),
        ),
        "candidate_literal_count": len(_stable_positive_literals(model)),
        "candidate_guard_count": 1 << len(_stable_positive_literals(model)),
        "consistent_hypothesis_count": len(hypotheses),
        "hypotheses": [hypothesis.as_dict() for hypothesis in hypotheses],
        "distinguishing_probe_count": len(probes),
        "best_probe": probes[0] if probes else None,
        "ranked_probes": probes,
    }
    report = dict(core)
    report["report_digest"] = document_digest(
        "actionSemanticsVersionSpaceReport",
        REPORT_DIGEST_SCHEMA,
        core,
    )
    return report


def verify_report(model: VersionSpaceModel, report: Any) -> dict[str, Any]:
    if not isinstance(report, dict):
        raise ValidationError("version-space report: expected an object")
    expected = solve_model(model)
    if report != expected:
        raise ValidationError(
            "version-space report does not match exact recomputation"
        )
    return report
