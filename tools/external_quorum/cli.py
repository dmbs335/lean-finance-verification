from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.evidence_synth.canonical import load_json

from .errors import ExternalQuorumError, ValidationError
from .quorum import verify_quorum
from .receipt import load_receipt, verify_receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lfv-external-quorum")
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--openssl", default="openssl")
    args = parser.parse_args(argv)
    try:
        policy = load_json(args.policy)
        if not isinstance(policy, dict):
            raise ValidationError("policy must be an object")
        verified = []
        for item in policy.get("receipts", []):
            verified.append(verify_receipt(
                load_receipt(Path(item["receipt"])),
                Path(item["public_key"]),
                policy["cutoff"],
                openssl_binary=args.openssl,
            ))
        report = verify_quorum(
            verified,
            target_digest=policy["target_digest"],
            cutoff=policy["cutoff"],
            required_domains=policy["required_domains"],
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(report, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        print(
            f"domains={report['domain_count']} providers={len(report['providers'])}"
        )
        return 0
    except (ExternalQuorumError, OSError, KeyError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
