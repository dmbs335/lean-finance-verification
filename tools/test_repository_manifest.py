from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.repository_manifest import SCHEMA_VERSION, build_manifest, canonical_file_bytes


class RepositoryManifestTests(unittest.TestCase):
    def test_text_identity_is_independent_of_line_endings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "source.py"
            path.write_bytes(b"first\r\nsecond\r\n")
            crlf = canonical_file_bytes(path)
            path.write_bytes(b"first\nsecond\n")
            lf = canonical_file_bytes(path)
            self.assertEqual(crlf, lf)
            self.assertEqual(hashlib.sha256(crlf).digest(), hashlib.sha256(lf).digest())

    def test_manifest_is_sorted_and_self_describing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "a.txt").write_text("a\n", encoding="utf-8")
            (root / "z.txt").write_text("z\n", encoding="utf-8")
            manifest = build_manifest(root, ["z.txt", "a.txt"])
            self.assertEqual(manifest["schema_version"], SCHEMA_VERSION)
            self.assertEqual(
                [entry["path"] for entry in manifest["files"]],
                ["a.txt", "z.txt"],
            )


if __name__ == "__main__":
    unittest.main()
