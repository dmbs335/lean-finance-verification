from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.evidence_synth.canonical import load_json

from .errors import SelectiveReceiptError, ValidationError
from .policy import load_policy
from .receipt import issue_receipt, verify_receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lfv-selective-receipt")
    sub = parser.add_subparsers(dest="command", required=True)
    issue = sub.add_parser("issue")
    issue.add_argument("--policy", required=True, type=Path)
    issue.add_argument("--events", required=True, type=Path)
    issue.add_argument("--private-key", required=True, type=Path)
    issue.add_argument("--public-key", required=True, type=Path)
    issue.add_argument("--salt-seed", required=True)
    issue.add_argument("--finished-at", required=True, type=int)
    issue.add_argument("--out", required=True, type=Path)
    check = sub.add_parser("verify")
    check.add_argument("--policy", required=True, type=Path)
    check.add_argument("--receipt", required=True, type=Path)
    check.add_argument("--public-key", required=True, type=Path)
    check.add_argument("--cutoff", required=True, type=int)
    check.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        policy = load_policy(args.policy)
        if args.command == "issue":
            events = load_json(args.events)
            if not isinstance(events, list) or any(not isinstance(item, str) for item in events):
                raise ValidationError("events must be an array of action strings")
            result = issue_receipt(
                policy, events, salt_seed_hex=args.salt_seed,
                private_key=args.private_key, public_key=args.public_key,
                finished_at=args.finished_at,
            )
        else:
            result = verify_receipt(
                policy, load_json(args.receipt), args.public_key,
                cutoff=args.cutoff,
            )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(result, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        return 0
    except (SelectiveReceiptError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
