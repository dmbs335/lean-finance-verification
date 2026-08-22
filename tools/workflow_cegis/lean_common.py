from __future__ import annotations

import re

from .explore import ExpandedChannel, History

_LEAN_KEYWORDS = {
    "abbrev", "axiom", "by", "class", "def", "deriving", "do", "else",
    "end", "example", "export", "extends", "false", "forall", "fun", "if",
    "import", "in", "inductive", "infix", "instance", "let", "match",
    "namespace", "open", "opaque", "private", "protected", "structure",
    "syntax", "theorem", "true", "universe", "variable", "where", "with",
}


def lean_identifier(value: str, *, prefix: str) -> str:
    identifier = re.sub(r"[^A-Za-z0-9_]", "_", value)
    identifier = re.sub(r"_+", "_", identifier).strip("_")
    if not identifier:
        identifier = prefix
    identifier = identifier[0].lower() + identifier[1:]
    if identifier[0].isdigit():
        identifier = f"{prefix}_{identifier}"
    if identifier in _LEAN_KEYWORDS:
        identifier = f"{prefix}_{identifier}"
    return identifier


def unique_identifiers(values: list[str], prefix: str) -> dict[str, str]:
    used: set[str] = set()
    result: dict[str, str] = {}
    for value in values:
        base = lean_identifier(value, prefix=prefix)
        candidate = base
        counter = 2
        while candidate in used:
            candidate = f"{base}_{counter}"
            counter += 1
        used.add(candidate)
        result[value] = candidate
    return result


def lean_string(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def lean_list(items: list[str]) -> str:
    return "[" + ", ".join(items) + "]"


def _render_inductive(name: str, constructors: list[str]) -> list[str]:
    lines = [f"inductive {name} where"]
    lines.extend(f"  | {constructor}" for constructor in constructors)
    lines.append("  deriving Repr, DecidableEq")
    lines.append("")
    return lines


def _history_channel_maps(
    histories: tuple[History, ...], channels: tuple[ExpandedChannel, ...]
) -> tuple[dict[str, str], dict[str, str]]:
    return (
        unique_identifiers([history.id for history in histories], "history"),
        unique_identifiers([channel.id for channel in channels], "channel"),
    )
