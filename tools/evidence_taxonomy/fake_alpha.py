from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes, load_json

SCHEMA = "lfv-fake-alpha-benchmark-v1"
REPORT_SCHEMA = "lfv-fake-alpha-benchmark-report-v1"


class FakeAlphaValidationError(ValueError):
    """Raised when a benchmark or report violates the declared schema."""


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FakeAlphaValidationError(f"{path}: expected object")
    return value


def _integer(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise FakeAlphaValidationError(f"{path}: expected integer")
    return value


def _natural(value: Any, path: str) -> int:
    result = _integer(value, path)
    if result < 0:
        raise FakeAlphaValidationError(f"{path}: expected non-negative integer")
    return result


def _identifier(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise FakeAlphaValidationError(f"{path}: expected non-empty string")
    return value


@dataclass(frozen=True)
class Architecture:
    id: str
    channels: tuple[str, ...]


@dataclass(frozen=True)
class Attack:
    id: str
    separators: tuple[str, ...]


@dataclass(frozen=True)
class Scenario:
    id: str
    attack: str | None
    economic_alpha_bps: int
    attack_bias_bps: int
    model_bias_bps: int
    sampling_noise_bps: int

    @property
    def observed_alpha_bps(self) -> int:
        return (
            self.attack_bias_bps
            + self.economic_alpha_bps
            + self.model_bias_bps
            + self.sampling_noise_bps
        )


@dataclass(frozen=True)
class Benchmark:
    source: Path
    name: str
    model_uncertainty_bps: int
    sampling_uncertainty_bps: int
    architectures: tuple[Architecture, ...]
    attacks: tuple[Attack, ...]
    scenarios: tuple[Scenario, ...]

    @property
    def attack_by_id(self) -> dict[str, Attack]:
        return {attack.id: attack for attack in self.attacks}


def load_benchmark(path: Path) -> Benchmark:
    raw = _object(load_json(path), "$")
    expected = {
        "schema_version",
        "name",
        "model_uncertainty_bps",
        "sampling_uncertainty_bps",
        "architectures",
        "attacks",
        "scenarios",
    }
    if set(raw) != expected or raw["schema_version"] != SCHEMA:
        raise FakeAlphaValidationError("$: fields or schema do not match")

    architectures: list[Architecture] = []
    known_channels: set[str] = set()
    for index, item in enumerate(raw["architectures"]):
        obj = _object(item, f"$.architectures[{index}]")
        architecture_id = _identifier(obj.get("id"), f"$.architectures[{index}].id")
        channels = tuple(obj.get("channels", []))
        if any(not isinstance(channel, str) or not channel for channel in channels):
            raise FakeAlphaValidationError(
                f"$.architectures[{index}].channels: expected strings"
            )
        if len(set(channels)) != len(channels):
            raise FakeAlphaValidationError(
                f"$.architectures[{index}].channels: duplicates"
            )
        known_channels.update(channels)
        architectures.append(Architecture(architecture_id, channels))
    if not architectures or len({item.id for item in architectures}) != len(architectures):
        raise FakeAlphaValidationError("$.architectures: expected unique non-empty entries")

    attacks: list[Attack] = []
    for index, item in enumerate(raw["attacks"]):
        obj = _object(item, f"$.attacks[{index}]")
        attack_id = _identifier(obj.get("id"), f"$.attacks[{index}].id")
        separators = tuple(obj.get("separators", []))
        if not separators or any(
            not isinstance(channel, str) or not channel for channel in separators
        ):
            raise FakeAlphaValidationError(
                f"$.attacks[{index}].separators: expected non-empty strings"
            )
        if len(set(separators)) != len(separators):
            raise FakeAlphaValidationError(
                f"$.attacks[{index}].separators: duplicates"
            )
        known_channels.update(separators)
        attacks.append(Attack(attack_id, separators))
    if not attacks or len({item.id for item in attacks}) != len(attacks):
        raise FakeAlphaValidationError("$.attacks: expected unique non-empty entries")
    attack_ids = {attack.id for attack in attacks}

    scenarios: list[Scenario] = []
    for index, item in enumerate(raw["scenarios"]):
        obj = _object(item, f"$.scenarios[{index}]")
        attack = obj.get("attack")
        if attack is not None and attack not in attack_ids:
            raise FakeAlphaValidationError(
                f"$.scenarios[{index}].attack: unknown attack"
            )
        attack_bias = _integer(
            obj.get("attack_bias_bps"), f"$.scenarios[{index}].attack_bias_bps"
        )
        if attack is None and attack_bias != 0:
            raise FakeAlphaValidationError(
                f"$.scenarios[{index}]: clean scenario must have zero attack bias"
            )
        scenarios.append(
            Scenario(
                id=_identifier(obj.get("id"), f"$.scenarios[{index}].id"),
                attack=attack,
                economic_alpha_bps=_integer(
                    obj.get("economic_alpha_bps"),
                    f"$.scenarios[{index}].economic_alpha_bps",
                ),
                attack_bias_bps=attack_bias,
                model_bias_bps=_integer(
                    obj.get("model_bias_bps"),
                    f"$.scenarios[{index}].model_bias_bps",
                ),
                sampling_noise_bps=_integer(
                    obj.get("sampling_noise_bps"),
                    f"$.scenarios[{index}].sampling_noise_bps",
                ),
            )
        )
    if not scenarios or len({item.id for item in scenarios}) != len(scenarios):
        raise FakeAlphaValidationError("$.scenarios: expected unique non-empty entries")

    return Benchmark(
        source=path.resolve(),
        name=_identifier(raw["name"], "$.name"),
        model_uncertainty_bps=_natural(
            raw["model_uncertainty_bps"], "$.model_uncertainty_bps"
        ),
        sampling_uncertainty_bps=_natural(
            raw["sampling_uncertainty_bps"], "$.sampling_uncertainty_bps"
        ),
        architectures=tuple(architectures),
        attacks=tuple(attacks),
        scenarios=tuple(scenarios),
    )


def _evaluate_architecture(
    benchmark: Benchmark, architecture: Architecture
) -> dict[str, Any]:
    channels = set(architecture.channels)
    attack_count = sum(scenario.attack is not None for scenario in benchmark.scenarios)
    detected_count = 0
    certifiable_count = 0
    unremoved_attack_bias = 0
    scenarios: list[dict[str, Any]] = []
    radius = benchmark.model_uncertainty_bps + benchmark.sampling_uncertainty_bps

    for scenario in benchmark.scenarios:
        if scenario.attack is None:
            detected = True
            separators: tuple[str, ...] = tuple()
        else:
            attack = benchmark.attack_by_id[scenario.attack]
            separators = attack.separators
            detected = not channels.isdisjoint(separators)
            if detected:
                detected_count += 1
            else:
                unremoved_attack_bias += abs(scenario.attack_bias_bps)

        certifiable = detected
        removed_bias = scenario.attack_bias_bps if scenario.attack and detected else 0
        cleaned = scenario.observed_alpha_bps - removed_bias
        interval = None
        contains_economic_alpha = None
        if certifiable:
            certifiable_count += 1
            lower = cleaned - radius
            upper = cleaned + radius
            interval = {"lower_bps": lower, "upper_bps": upper}
            contains_economic_alpha = (
                lower <= scenario.economic_alpha_bps <= upper
            )
            if not contains_economic_alpha:
                raise FakeAlphaValidationError(
                    f"scenario {scenario.id}: declared uncertainty misses ground truth"
                )

        scenarios.append(
            {
                "id": scenario.id,
                "attack": scenario.attack,
                "separators": list(separators),
                "detected": detected,
                "certifiable": certifiable,
                "economic_alpha_bps": scenario.economic_alpha_bps,
                "observed_alpha_bps": scenario.observed_alpha_bps,
                "removed_attack_bias_bps": removed_bias,
                "cleaned_alpha_bps": cleaned,
                "certifiable_interval": interval,
                "interval_contains_economic_alpha": contains_economic_alpha,
            }
        )

    return {
        "id": architecture.id,
        "channels": list(architecture.channels),
        "attack_count": attack_count,
        "detected_attack_count": detected_count,
        "certifiable_scenario_count": certifiable_count,
        "unremoved_attack_bias_bps": unremoved_attack_bias,
        "scenarios": scenarios,
    }


def evaluate(benchmark: Benchmark) -> dict[str, Any]:
    architecture_results = [
        _evaluate_architecture(benchmark, architecture)
        for architecture in benchmark.architectures
    ]
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": benchmark.name,
        "scenario_count": len(benchmark.scenarios),
        "attack_scenario_count": sum(
            scenario.attack is not None for scenario in benchmark.scenarios
        ),
        "model_uncertainty_bps": benchmark.model_uncertainty_bps,
        "sampling_uncertainty_bps": benchmark.sampling_uncertainty_bps,
        "architectures": architecture_results,
    }
    report["report_sha256"] = hashlib.sha256(canonical_bytes(report)).hexdigest()
    return report


def verify(benchmark: Benchmark, report: Any) -> dict[str, Any]:
    expected = evaluate(benchmark)
    if report != expected:
        raise FakeAlphaValidationError(
            "fake-alpha benchmark report does not match exact recomputation"
        )
    return expected
