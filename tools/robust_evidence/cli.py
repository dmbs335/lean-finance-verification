from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.evidence_synth.canonical import (
    canonical_bytes,
    load_json,
    write_canonical_json,
    write_pretty_json,
)
from tools.evidence_synth.model import load_model

from .errors import RobustEvidenceError, ValidationError
from .policy import load_policy
from .solver import solve_robust, verify_certificate


def _path(value: str) -> Path:
    return Path(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lfv-robust-evidence",
        description=(
            "Synthesize minimum-cost evidence portfolios resilient to declared "
            "trust-domain fault scenarios"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    synth = subparsers.add_parser("synth", help="solve one robust evidence policy")
    synth.add_argument("--model", required=True, type=_path)
    synth.add_argument("--policy", required=True, type=_path)
    synth.add_argument("--out", required=True, type=_path)
    synth.add_argument("--pretty", action="store_true")

    verify = subparsers.add_parser(
        "verify", help="recompute and verify a robust synthesis artifact"
    )
    verify.add_argument("--model", required=True, type=_path)
    verify.add_argument("--policy", required=True, type=_path)
    verify.add_argument("--certificate", required=True, type=_path)

    check = subparsers.add_parser(
        "check-generated",
        help="fail when a checked-in robust certificate has drifted",
    )
    check.add_argument("--model", required=True, type=_path)
    check.add_argument("--policy", required=True, type=_path)
    check.add_argument("--certificate", required=True, type=_path)
    return parser


def _load(model_path: Path, policy_path: Path):
    model = load_model(model_path)
    policy = load_policy(policy_path, model)
    return model, policy


def _command_synth(args: argparse.Namespace) -> None:
    model, policy = _load(args.model, args.policy)
    certificate = solve_robust(model, policy)
    write_canonical_json(args.out, certificate)
    if args.pretty:
        write_pretty_json(args.out.with_suffix(".pretty.json"), certificate)
    print(f"wrote {args.out}")
    print(
        "selected=" + ",".join(certificate["selected"]["channels"])
        + f" cost={certificate['selected']['weighted_cost']}"
    )


def _command_verify(args: argparse.Namespace) -> None:
    model, policy = _load(args.model, args.policy)
    verify_certificate(model, policy, load_json(args.certificate))
    print(f"verified {args.certificate}")


def _command_check(args: argparse.Namespace) -> None:
    model, policy = _load(args.model, args.policy)
    expected = solve_robust(model, policy)
    if args.certificate.read_bytes() != canonical_bytes(expected):
        raise ValidationError(
            f"robust evidence certificate drift: regenerate {args.certificate}"
        )
    print("generated robust evidence certificate is reproducible")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "synth":
            _command_synth(args)
        elif args.command == "verify":
            _command_verify(args)
        elif args.command == "check-generated":
            _command_check(args)
        else:
            parser.error(f"unknown command: {args.command}")
        return 0
    except (RobustEvidenceError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
