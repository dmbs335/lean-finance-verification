from __future__ import annotations

import copy
import unittest

from tools.lfv_adapter.canonical import make_artifact_ref
from tools.lfv_adapter.errors import ValidationError
from tools.lfv_adapter.ledger import (
    append_trial,
    empty_ledger,
    make_local_anchor,
    verify_anchor,
    verify_ledger,
)


def ref(kind: str, value: int) -> dict[str, str]:
    artifact, _ = make_artifact_ref(
        kind=kind,
        schema_id=f"{kind}-v1",
        payload={"value": value},
        algorithm="sha256",
    )
    return artifact


class LedgerTests(unittest.TestCase):
    def test_append_only_chain_and_anchor_are_verified(self) -> None:
        first = append_trial(
            empty_ledger(),
            hypothesis_id="h1",
            parameters=ref("parameterSet", 1),
            code=ref("sourceCode", 1),
            registered_at=10,
            algorithm="sha256",
        )
        second = append_trial(
            first,
            hypothesis_id="h2",
            parameters=ref("parameterSet", 2),
            code=ref("sourceCode", 2),
            registered_at=11,
            algorithm="sha256",
        )
        verified = verify_ledger(second)
        self.assertEqual(len(verified["entries"]), 2)
        anchor = make_local_anchor(verified, anchored_at=12)
        with self.assertRaisesRegex(ValidationError, "local-development"):
            verify_anchor(anchor, verified, cutoff_time=20)
        verified_anchor = verify_anchor(
            anchor, verified, cutoff_time=20, allow_local=True
        )
        self.assertEqual(verified_anchor["entry_count"], 2)

    def test_commitment_tampering_is_detected(self) -> None:
        ledger = append_trial(
            empty_ledger(),
            hypothesis_id="h1",
            parameters=ref("parameterSet", 1),
            code=ref("sourceCode", 1),
            registered_at=10,
            algorithm="sha256",
        )
        tampered = copy.deepcopy(ledger)
        tampered["entries"][0]["hypothesis_id"] = "changed"
        with self.assertRaisesRegex(ValidationError, "digest mismatch"):
            verify_ledger(tampered)

    def test_non_monotone_registration_time_is_rejected(self) -> None:
        ledger = append_trial(
            empty_ledger(),
            hypothesis_id="h1",
            parameters=ref("parameterSet", 1),
            code=ref("sourceCode", 1),
            registered_at=10,
            algorithm="sha256",
        )
        with self.assertRaisesRegex(ValidationError, "precedes"):
            append_trial(
                ledger,
                hypothesis_id="h2",
                parameters=ref("parameterSet", 2),
                code=ref("sourceCode", 2),
                registered_at=9,
                algorithm="sha256",
            )


if __name__ == "__main__":
    unittest.main()
