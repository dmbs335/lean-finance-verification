from __future__ import annotations

from pathlib import Path

from .errors import ValidationError


def resolve_under(base: Path, relative: str, *, must_exist: bool = True) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ValidationError("path must be a non-empty string")
    candidate_input = Path(relative)
    if candidate_input.is_absolute():
        raise ValidationError(f"absolute paths are not allowed: {relative}")
    base_resolved = base.resolve()
    candidate = (base_resolved / candidate_input).resolve()
    try:
        candidate.relative_to(base_resolved)
    except ValueError as exc:
        raise ValidationError(f"path escapes experiment root: {relative}") from exc
    if must_exist and not candidate.exists():
        raise ValidationError(f"missing path: {relative}")
    return candidate


def logical_path(base: Path, path: Path) -> str:
    return path.resolve().relative_to(base.resolve()).as_posix()
