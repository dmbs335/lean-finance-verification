from __future__ import annotations

import re
from pathlib import Path

from .bundle_build import (
    BuildResult,
    build_bundle,
    compute_code_artifact,
    compute_dataset_artifact,
    compute_json_artifact,
    compute_preregistration_artifacts,
    resolve_pointer,
    run_empirical_command,
)
from .bundle_verify import verify_bundle
from .canonical import write_canonical_json, write_pretty_json
from .rfc3161 import Rfc3161Trust
from .spec import load_experiment_spec


_LINEAGE_DATASET_SIMP = re.compile(
    r"(?P<prefix>\s*· simp \[DatasetAvailableAt, dataset_[A-Za-z0-9_]+), "
    r"featureLineage_(?P<feature>[A-Za-z0-9_]+)\]"
)


def _stabilize_generated_lineage_proofs(source: str) -> str:
    """Expose the derived-feature alias needed by Lean's simplifier.

    The core renderer keeps lineage definitions compact. When the stronger
    time-indexed lineage predicate asks for an input at a feature's own
    generation timestamp, Lean must also unfold the corresponding
    ``DerivedFeature`` alias. This deterministic normalization is a no-op for
    renderers that already include that alias.
    """

    return _LINEAGE_DATASET_SIMP.sub(
        lambda match: (
            f"{match.group('prefix')}, derivedFeature_{match.group('feature')}, "
            f"featureLineage_{match.group('feature')}]"
        ),
        source,
    )


def build_from_spec(
    spec_path: Path,
    *,
    allow_local_anchor: bool = False,
    rfc3161_trust: Rfc3161Trust | None = None,
) -> BuildResult:
    from .lean import render_lean

    spec = load_experiment_spec(spec_path)
    bundle, result_payload = build_bundle(
        spec,
        allow_local_anchor=allow_local_anchor,
        rfc3161_trust=rfc3161_trust,
    )
    lean_source = _stabilize_generated_lineage_proofs(render_lean(bundle))
    return BuildResult(
        spec=spec,
        bundle=bundle,
        result_payload=result_payload,
        lean_source=lean_source,
    )


def write_build_result(result: BuildResult, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_canonical_json(output_dir / "bundle.canonical.json", result.bundle)
    write_pretty_json(output_dir / "bundle.pretty.json", result.bundle)
    write_canonical_json(
        output_dir / "execution-result.canonical.json", result.result_payload
    )
    (output_dir / "GeneratedCertificate.lean").write_text(
        result.lean_source,
        encoding="utf-8",
    )
