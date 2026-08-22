from __future__ import annotations

import base64
import copy
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.selective_receipt.policy import load_policy
from tools.zk_receipt.errors import ValidationError
from tools.zk_receipt.group import load_parameters
from tools.zk_receipt.receipt import issue_receipt, verify_receipt

ROOT = Path(__file__).resolve().parents[3]
POLICY = ROOT / "examples" / "selective_receipt" / "policy.json"
PARAMETERS = ROOT / "examples" / "zk_receipt" / "experimental-group.json"


@unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required")
class ZKReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="lfv-zk-")
        self.root = Path(self.temporary.name)
        self.private = self.root / "runner.key"
        self.public = self.root / "runner.pub"
        self._run(["genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(self.private)])
        self._run(["pkey", "-in", str(self.private), "-pubout", "-out", str(self.public)])
        self.policy = load_policy(POLICY)
        self.parameters = load_parameters(PARAMETERS)
        self.events = ["register", "executeBaseline", "publish", "anchor"]
        self.receipt = issue_receipt(
            self.policy, self.parameters, self.events,
            blinding_seed=b"B" * 32, nonce_seed=b"N" * 32,
            private_key=self.private, public_key=self.public, finished_at=8,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _run(self, args: list[str]) -> None:
        result = subprocess.run(
            [shutil.which("openssl") or "openssl", *args],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False, timeout=30,
        )
        if result.returncode != 0:
            self.fail(result.stderr.decode("utf-8", errors="replace"))

    def test_clean_receipt_verifies_without_opening_counts(self) -> None:
        verified = verify_receipt(self.policy, self.parameters, self.receipt, self.public, cutoff=10)
        self.assertEqual(verified["forbidden_absent"], list(self.policy.forbidden_actions))
        for proof in self.receipt["proofs"]:
            self.assertNotIn("count", proof)
            self.assertNotIn("blinding", proof)

    def test_nonzero_forbidden_count_cannot_issue_zero_proof(self) -> None:
        with self.assertRaisesRegex(ValidationError, "open to zero"):
            issue_receipt(
                self.policy, self.parameters, self.events + ["executeHiddenSweep"],
                blinding_seed=b"B" * 32, nonce_seed=b"N" * 32,
                private_key=self.private, public_key=self.public, finished_at=8,
            )

    def test_tampered_zero_proof_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.receipt)
        tampered["proofs"][0]["zero_proof"]["response"] = "1"
        with self.assertRaisesRegex(ValidationError, "Schnorr proof"):
            verify_receipt(self.policy, self.parameters, tampered, self.public, cutoff=10)

    def test_tampered_commitment_membership_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.receipt)
        tampered["proofs"][0]["commitment"] = "2"
        with self.assertRaisesRegex(ValidationError, "committed histogram root"):
            verify_receipt(self.policy, self.parameters, tampered, self.public, cutoff=10)

    def test_parameter_substitution_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.receipt)
        tampered["parameter_digest"] = "00" * 32
        with self.assertRaisesRegex(ValidationError, "different ZK parameters"):
            verify_receipt(self.policy, self.parameters, tampered, self.public, cutoff=10)

    def test_signature_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.receipt)
        signature = bytearray(base64.b64decode(tampered["signature_base64"]))
        signature[-1] ^= 1
        tampered["signature_base64"] = base64.b64encode(signature).decode("ascii")
        with self.assertRaisesRegex(ValidationError, "signature verification"):
            verify_receipt(self.policy, self.parameters, tampered, self.public, cutoff=10)

    def test_deterministic_test_transcript(self) -> None:
        second = issue_receipt(
            self.policy, self.parameters, self.events,
            blinding_seed=b"B" * 32, nonce_seed=b"N" * 32,
            private_key=self.private, public_key=self.public, finished_at=8,
        )
        self.assertEqual(self.receipt, second)


if __name__ == "__main__":
    unittest.main()
