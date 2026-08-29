from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable


SCHEMA_VERSION = "lfv-repository-manifest-v2"
MANIFEST_NAME = "MANIFEST.json"


def canonical_file_bytes(path: Path) -> bytes:
    """Canonicalize repository text so checkout line endings do not alter identity."""
    text = path.read_bytes().decode("utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def repository_paths(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    paths = result.stdout.decode("utf-8").split("\0")
    return sorted(
        path
        for path in paths
        if path and path != MANIFEST_NAME and (root / path).is_file()
    )


def build_manifest(root: Path, paths: Iterable[str] | None = None) -> dict[str, object]:
    selected = repository_paths(root) if paths is None else sorted(paths)
    files: list[dict[str, object]] = []
    for relative in selected:
        payload = canonical_file_bytes(root / relative)
        files.append(
            {
                "path": relative.replace("\\", "/"),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "bytes": len(payload),
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "hash_algorithm": "sha256",
        "text_normalization": "utf-8-lf",
        "excluded_paths": [MANIFEST_NAME],
        "files": files,
    }


def serialized_manifest(manifest: dict[str, object]) -> str:
    return json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"


def generate(root: Path) -> None:
    (root / MANIFEST_NAME).write_text(
        serialized_manifest(build_manifest(root)), encoding="utf-8", newline="\n"
    )


def check(root: Path) -> bool:
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.is_file():
        print(f"error: missing {MANIFEST_NAME}", file=sys.stderr)
        return False
    expected = serialized_manifest(build_manifest(root))
    actual = manifest_path.read_text(encoding="utf-8")
    if actual != expected:
        print(
            f"error: {MANIFEST_NAME} is stale; run "
            "python -m tools.repository_manifest generate",
            file=sys.stderr,
        )
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or verify the repository manifest")
    parser.add_argument("command", choices=("generate", "check"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.command == "generate":
        generate(root)
        print(f"wrote {MANIFEST_NAME}")
        return 0
    if not check(root):
        return 2
    print(f"{MANIFEST_NAME} is current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
