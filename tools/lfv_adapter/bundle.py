from __future__ import annotations

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
from .spec import load_experiment_spec


def build_from_spec(
    spec_path: Path,
    *,
    allow_local_anchor: bool = False,
) -> BuildResult:
    from .lean import render_lean

    spec = load_experiment_spec(spec_path)
    bundle, result_payload = build_bundle(spec, allow_local_anchor=allow_local_anchor)
    lean_source = render_lean(bundle)
    return BuildResult(spec=spec, bundle=bundle, result_payload=result_payload, lean_source=lean_source)


def write_build_result(result: BuildResult, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_canonical_json(output_dir / "bundle.canonical.json", result.bundle)
    write_pretty_json(output_dir / "bundle.pretty.json", result.bundle)
    write_canonical_json(output_dir / "execution-result.canonical.json", result.result_payload)
    (output_dir / "GeneratedCertificate.lean").write_text(
        result.lean_source,
        encoding="utf-8",
    )
