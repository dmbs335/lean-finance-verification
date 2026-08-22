from __future__ import annotations

import copy
import csv
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.pit_study.checker import check
from tools.pit_study.model import load_study
from tools.pit_vendor_import.errors import ValidationError
from tools.pit_vendor_import.importer import import_study
from tools.pit_vendor_import.manifest import build_manifest
from tools.evidence_synth.canonical import load_json

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "examples" / "pit_vendor_package"


@unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required")
class VendorImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="lfv-vendor-")
        self.root = Path(self.temporary.name)
        self.package = self.root / "package"
        shutil.copytree(FIXTURE / "package", self.package)
        self.private = self.root / "vendor.key"
        self.public = self.root / "vendor.pub"
        self._run(["genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(self.private)])
        self._run(["pkey", "-in", str(self.private), "-pubout", "-out", str(self.public)])
        self.manifest = build_manifest(
            FIXTURE / "metadata.json", self.package,
            self.public, self.private, signed_at=50,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _run(self, args: list[str]) -> None:
        result = subprocess.run(
            [shutil.which("openssl") or "openssl", *args],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False, timeout=30,
        )
        if result.returncode != 0:
            self.fail(result.stderr.decode("utf-8", errors="replace"))

    def _import(self):
        return import_study(
            self.manifest, self.package, self.public,
            FIXTURE / "research-plan.json",
        )

    def test_signed_package_imports_into_valid_pit_study(self) -> None:
        study, report = self._import()
        path = self.root / "study.json"
        path.write_text(json.dumps(study), encoding="utf-8")
        checked = check(load_study(path))
        self.assertEqual(checked["decisions"][0]["selected"], "BETA")
        self.assertEqual(report["vintage_count"], 2)
        self.assertEqual(report["asset_count"], 3)
        self.assertEqual(report["package"]["license_id"], "fixture-license-v1")

    def test_file_tampering_is_rejected(self) -> None:
        with (self.package / "prices.csv").open("a", encoding="utf-8") as handle:
            handle.write("ALPHA,50,51,120,prices-v1\n")
        with self.assertRaisesRegex(ValidationError, "digest, row count, or schema"):
            self._import()

    def test_signature_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.manifest)
        tampered["vendor_id"] = "attacker"
        with self.assertRaisesRegex(ValidationError, "signature verification"):
            import_study(tampered, self.package, self.public,
                FIXTURE / "research-plan.json")

    def test_public_key_substitution_is_rejected(self) -> None:
        wrong_private = self.root / "wrong.key"
        wrong_public = self.root / "wrong.pub"
        self._run(["genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(wrong_private)])
        self._run(["pkey", "-in", str(wrong_private), "-pubout", "-out", str(wrong_public)])
        with self.assertRaisesRegex(ValidationError, "public key"):
            import_study(self.manifest, self.package, wrong_public,
                FIXTURE / "research-plan.json")

    def test_nonmonotone_revision_is_rejected_after_resigning(self) -> None:
        path = self.package / "vintages.csv"
        rows = list(csv.DictReader(path.open("r", encoding="utf-8", newline="")))
        rows[1]["first_published_at"] = "0"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["id", "revision", "first_published_at", "supersedes"])
            writer.writeheader()
            writer.writerows(rows)
        manifest = build_manifest(FIXTURE / "metadata.json", self.package,
            self.public, self.private, signed_at=50)
        with self.assertRaisesRegex(ValidationError, "revision chain"):
            import_study(manifest, self.package, self.public,
                FIXTURE / "research-plan.json")

    def test_missing_license_is_rejected(self) -> None:
        metadata = load_json(FIXTURE / "metadata.json")
        metadata["license_id"] = ""
        path = self.root / "metadata.json"
        path.write_text(json.dumps(metadata), encoding="utf-8")
        with self.assertRaisesRegex(ValidationError, "license_id"):
            build_manifest(path, self.package, self.public, self.private, signed_at=50)

    def test_deterministic_import(self) -> None:
        first = self._import()
        second = self._import()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
