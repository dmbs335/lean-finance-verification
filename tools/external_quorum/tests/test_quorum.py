from __future__ import annotations

import base64
import copy
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.external_quorum.errors import ValidationError
from tools.external_quorum.merkle import build_tree, inclusion_proof
from tools.external_quorum.quorum import verify_quorum
from tools.external_quorum.receipt import (
    public_key_sha256,
    sign_tree_head,
    tree_head_payload,
    verify_receipt,
)


@unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required")
class ExternalQuorumTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="lfv-quorum-")
        self.root = Path(self.temporary.name)
        self.target = "11" * 32

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _run(self, arguments: list[str]) -> None:
        completed = subprocess.run(
            [shutil.which("openssl") or "openssl", *arguments],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
        if completed.returncode != 0:
            self.fail(completed.stderr.decode("utf-8", errors="replace"))

    def _keypair(self, name: str) -> tuple[Path, Path]:
        private = self.root / f"{name}.key"
        public = self.root / f"{name}.pub"
        self._run([
            "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048",
            "-out", str(private),
        ])
        self._run(["pkey", "-in", str(private), "-pubout", "-out", str(public)])
        return private, public

    def _receipt(self, provider: str, domain: str, anchored_at: int):
        private, public = self._keypair(provider)
        leaves = ["00" * 32, self.target, "22" * 32, "33" * 32]
        levels = build_tree(leaves)
        receipt = {
            "schema_version": "lfv-signed-transparency-receipt-v1",
            "provider_id": provider,
            "trust_domain": domain,
            "target_digest": self.target,
            "leaf_index": 1,
            "tree_size": 4,
            "root_sha256": levels[-1][0].hex(),
            "audit_path": inclusion_proof(levels, 1),
            "anchored_at": anchored_at,
            "public_key_sha256": public_key_sha256(public),
            "signature_base64": "",
        }
        receipt["signature_base64"] = sign_tree_head(
            tree_head_payload(receipt), private
        )
        return receipt, public

    def test_two_independent_signed_logs_meet_quorum(self) -> None:
        first_raw, first_key = self._receipt("log-a", "operator-a", 8)
        second_raw, second_key = self._receipt("log-b", "operator-b", 9)
        first = verify_receipt(first_raw, first_key, 10)
        second = verify_receipt(second_raw, second_key, 10)
        report = verify_quorum(
            [first, second], target_digest=self.target,
            cutoff=10, required_domains=2,
        )
        self.assertEqual(report["domain_count"], 2)

    def test_same_domain_duplicates_do_not_meet_quorum(self) -> None:
        first_raw, first_key = self._receipt("log-a", "shared", 8)
        second_raw, second_key = self._receipt("log-b", "shared", 9)
        receipts = [
            verify_receipt(first_raw, first_key, 10),
            verify_receipt(second_raw, second_key, 10),
        ]
        with self.assertRaisesRegex(ValidationError, "trust domains"):
            verify_quorum(receipts, target_digest=self.target,
                cutoff=10, required_domains=2)

    def test_tampered_inclusion_path_is_rejected(self) -> None:
        raw, key = self._receipt("log-a", "operator-a", 8)
        raw["audit_path"][0]["digest"] = "ff" * 32
        with self.assertRaisesRegex(ValidationError, "inclusion proof"):
            verify_receipt(raw, key, 10)

    def test_tampered_signature_is_rejected(self) -> None:
        raw, key = self._receipt("log-a", "operator-a", 8)
        signature = bytearray(base64.b64decode(raw["signature_base64"]))
        signature[-1] ^= 1
        raw["signature_base64"] = base64.b64encode(signature).decode("ascii")
        with self.assertRaisesRegex(ValidationError, "signature verification"):
            verify_receipt(raw, key, 10)

    def test_verifier_selected_key_substitution_is_rejected(self) -> None:
        raw, _key = self._receipt("log-a", "operator-a", 8)
        _wrong_private, wrong_public = self._keypair("wrong")
        with self.assertRaisesRegex(ValidationError, "public key"):
            verify_receipt(raw, wrong_public, 10)

    def test_late_tree_head_is_rejected(self) -> None:
        raw, key = self._receipt("log-a", "operator-a", 11)
        with self.assertRaisesRegex(ValidationError, "later than"):
            verify_receipt(raw, key, 10)

    def test_target_mismatch_is_rejected_by_quorum(self) -> None:
        raw, key = self._receipt("log-a", "operator-a", 8)
        verified = verify_receipt(raw, key, 10)
        with self.assertRaisesRegex(ValidationError, "different target"):
            verify_quorum([verified], target_digest="22" * 32,
                cutoff=10, required_domains=1)


if __name__ == "__main__":
    unittest.main()
