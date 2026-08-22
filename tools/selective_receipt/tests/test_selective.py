from __future__ import annotations

import base64
import copy
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.selective_receipt.errors import ValidationError
from tools.selective_receipt.policy import load_policy
from tools.selective_receipt.receipt import issue_receipt, verify_receipt

ROOT = Path(__file__).resolve().parents[3]
POLICY = ROOT / "examples" / "selective_receipt" / "policy.json"


@unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required")
class SelectiveReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="lfv-selective-")
        self.root = Path(self.temporary.name)
        self.private = self.root / "runner.key"
        self.public = self.root / "runner.pub"
        self._run(["genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(self.private)])
        self._run(["pkey", "-in", str(self.private), "-pubout", "-out", str(self.public)])
        self.policy = load_policy(POLICY)
        self.events = ["register", "executeBaseline", "publish", "anchor"]
        self.seed = "42" * 32
        self.receipt = issue_receipt(
            self.policy, self.events, salt_seed_hex=self.seed,
            private_key=self.private, public_key=self.public,
            finished_at=8,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _run(self, args: list[str]) -> None:
        completed = subprocess.run(
            [shutil.which("openssl") or "openssl", *args],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False, timeout=30,
        )
        if completed.returncode != 0:
            self.fail(completed.stderr.decode("utf-8", errors="replace"))

    def test_clean_log_proves_forbidden_classes_absent(self) -> None:
        verified = verify_receipt(
            self.policy, self.receipt, self.public, cutoff=10
        )
        self.assertEqual(
            verified["forbidden_absent"],
            ["executeHiddenSweep", "readFutureData", "tamperCostModel"],
        )
        self.assertEqual(
            verified["disclosed_classes"], verified["forbidden_absent"]
        )

    def test_forbidden_event_is_rejected(self) -> None:
        receipt = issue_receipt(
            self.policy, self.events + ["executeHiddenSweep"],
            salt_seed_hex=self.seed, private_key=self.private,
            public_key=self.public, finished_at=8,
        )
        with self.assertRaisesRegex(ValidationError, "forbidden action occurred"):
            verify_receipt(self.policy, receipt, self.public, cutoff=10)

    def test_tampered_salt_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.receipt)
        tampered["disclosures"][0]["salt"] = "00" * 32
        with self.assertRaisesRegex(ValidationError, "committed histogram root"):
            verify_receipt(self.policy, tampered, self.public, cutoff=10)

    def test_tampered_signature_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.receipt)
        signature = bytearray(base64.b64decode(tampered["signature_base64"]))
        signature[-1] ^= 1
        tampered["signature_base64"] = base64.b64encode(signature).decode("ascii")
        with self.assertRaisesRegex(ValidationError, "signature verification"):
            verify_receipt(self.policy, tampered, self.public, cutoff=10)

    def test_missing_disclosure_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.receipt)
        tampered["disclosures"].pop()
        with self.assertRaisesRegex(ValidationError, "every forbidden"):
            verify_receipt(self.policy, tampered, self.public, cutoff=10)

    def test_public_key_substitution_is_rejected(self) -> None:
        wrong_private = self.root / "wrong.key"
        wrong_public = self.root / "wrong.pub"
        self._run(["genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(wrong_private)])
        self._run(["pkey", "-in", str(wrong_private), "-pubout", "-out", str(wrong_public)])
        with self.assertRaisesRegex(ValidationError, "public key"):
            verify_receipt(self.policy, self.receipt, wrong_public, cutoff=10)

    def test_unknown_action_cannot_be_hidden_outside_universe(self) -> None:
        with self.assertRaisesRegex(ValidationError, "unknown actions"):
            issue_receipt(
                self.policy, self.events + ["shadowAction"],
                salt_seed_hex=self.seed, private_key=self.private,
                public_key=self.public, finished_at=8,
            )

    def test_fixed_seed_is_deterministic(self) -> None:
        second = issue_receipt(
            self.policy, self.events, salt_seed_hex=self.seed,
            private_key=self.private, public_key=self.public,
            finished_at=8,
        )
        self.assertEqual(self.receipt, second)


if __name__ == "__main__":
    unittest.main()
