from __future__ import annotations

from typing import Any

from .explore import ExpandedChannel, History
from .lean_bridge import render_bridge_lean as _render_bridge_lean
from .lean_evidence import render_evidence_lean
from .lean_workflow import render_workflow_lean
from .model import WorkflowModel


def _use_kernel_chain_proof(source: str) -> str:
    """Replace the generated chain simplification with closed kernel computation.

    For larger repair bitmasks, Lean's simplifier can leave closed `Fin` coercion
    arithmetic unreduced even though the chain proposition is decidable. Replacing
    only that proof body with `decide` keeps the generated theorem semantic and
    avoids mask-specific simp lemmas.
    """

    theorem_marker = "theorem cegis_chain_connected :"
    proof_marker = " := by\n"
    next_marker = "\ndef proofCarryingCEGIS :"
    theorem_start = source.find(theorem_marker)
    if theorem_start < 0:
        return source
    proof_start = source.find(proof_marker, theorem_start)
    proof_end = source.find(next_marker, proof_start)
    if proof_start < 0 or proof_end < 0:
        raise ValueError("generated CEGIS chain proof markers are malformed")
    body_start = proof_start + len(proof_marker)
    return source[:body_start] + "  decide\n" + source[proof_end:]


def render_bridge_lean(
    model: WorkflowModel,
    report: dict[str, Any],
    histories: tuple[History, ...],
    channels: tuple[ExpandedChannel, ...],
) -> str:
    source = _render_bridge_lean(model, report, histories, channels)
    optional_channel_count = sum(not channel.deployed for channel in channels)
    if optional_channel_count >= 4:
        return _use_kernel_chain_proof(source)
    return source


__all__ = [
    "render_bridge_lean",
    "render_evidence_lean",
    "render_workflow_lean",
]
