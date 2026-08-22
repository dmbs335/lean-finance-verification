from __future__ import annotations

from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .receipt import VerifiedReceipt

REPORT_SCHEMA = "lfv-external-evidence-quorum-report-v1"


def verify_quorum(
    receipts: list[VerifiedReceipt],
    *,
    target_digest: str,
    cutoff: int,
    required_domains: int,
) -> dict[str, Any]:
    if required_domains <= 0:
        raise ValidationError("required domain count must be positive")
    if not receipts:
        raise ValidationError("quorum has no verified receipts")
    provider_ids = [receipt.provider_id for receipt in receipts]
    if len(set(provider_ids)) != len(provider_ids):
        raise ValidationError("duplicate provider ids do not increase quorum")
    for receipt in receipts:
        if receipt.target_digest != target_digest:
            raise ValidationError("provider receipts bind different target digests")
        if receipt.anchored_at > cutoff:
            raise ValidationError("provider receipt is later than cutoff")
    domains = sorted({receipt.trust_domain for receipt in receipts})
    if len(domains) < required_domains:
        raise ValidationError(
            f"quorum has {len(domains)} trust domains; {required_domains} required"
        )
    report = {
        "schema_version": REPORT_SCHEMA,
        "target_digest": target_digest,
        "cutoff": cutoff,
        "required_domains": required_domains,
        "providers": [receipt.as_dict() for receipt in receipts],
        "distinct_trust_domains": domains,
        "domain_count": len(domains),
    }
    report["report_sha256"] = __import__("hashlib").sha256(
        canonical_bytes(report)
    ).hexdigest()
    return report
