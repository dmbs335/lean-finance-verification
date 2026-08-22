from __future__ import annotations

import unittest

from tools.lfv_adapter.canonical import (
    canonical_dumps,
    make_artifact_ref,
    validate_digest,
)
from tools.lfv_adapter.errors import ValidationError


class CanonicalJsonTests(unittest.TestCase):
    def test_object_keys_are_sorted_without_insignificant_whitespace(self) -> None:
        self.assertEqual(canonical_dumps({"z": 1, "a": [True, None]}), '{"a":[true,null],"z":1}')

    def test_floating_point_values_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValidationError, "floating-point"):
            canonical_dumps({"value": 0.1})

    def test_domain_separation_changes_artifact_identity(self) -> None:
        payload = {"value": 1}
        dataset, _ = make_artifact_ref(
            kind="dataset", schema_id="schema-v1", payload=payload, algorithm="sha256"
        )
        result, _ = make_artifact_ref(
            kind="result", schema_id="schema-v1", payload=payload, algorithm="sha256"
        )
        self.assertNotEqual(dataset["digest"], result["digest"])

    def test_digest_shape_is_enforced(self) -> None:
        with self.assertRaises(ValidationError):
            validate_digest("sha256", "ABC")


if __name__ == "__main__":
    unittest.main()
