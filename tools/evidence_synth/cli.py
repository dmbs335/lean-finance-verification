from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .canonical import canonical_bytes, load_json, write_canonical_json, write_pretty_json
from .errors import SynthesisError
from .lean import render_lean
from .model import load_model
from .solver import solve_model, verify_certificate


def _path(value: str) -> Path:
    return Path(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lfv-evidence-synth",
        description=(
            "Exact bounded adversarial-history synthesis for minimum-cost "
            "evidence cut sets"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    synth = subparsers.add_parser(
        "synth", help="solve a bounded evidence model and emit JSON plus Lean"
    )
    synth.add_argument("--model", required=True, type=_path)
    synth.add_argument("--out", required=True, type=_path)
    synth.add_argument("--lean-out", required=True, type=_path)
    synth.add_argument("--pretty", action="store_true")
    verify = subparsers.add_parser(
        "verify", help="recompute and verify a synthesis certificate"
    )
    verify.add_argument("--model", required=True, type=_path)
    verify.add_argument("--certificate", required=True, type=_path)
    check = subparsers.add_parser(
        "check-generated",
        help="fail when checked-in synthesis JSON or generated Lean has drifted",
    )
    check.add_argument("--model", required=True, type=_path)
    check.add_argument("--certificate", required=True, type=_path)
    check.add_argument("--lean", required=True, type=_path)
    return parser


def _synthesize(model_path: Path) -> tuple[dict, str]:
    model = load_model(model_path)
    certificate = solve_model(model)
    lean_source = render_lean(model, certificate)
    return certificate, lean_source


def _command_synth(args: argparse.Namespace) -> None:
    certificate, lean_source = _synthesize(args.model)
    write_canonical_json(args.out, certificate)
    if args.pretty:
        write_pretty_json(args.out.with_suffix(".pretty.json"), certificate)
    args.lean_out.parent.mkdir(parents=True, exist_ok=True)
    args.lean_out.write_text(lean_source, encoding="utf-8")
    print(f"wrote {args.out}")
    print(f"wrote {args.lean_out}")
    if certificate["status"] == "synthesized":
        selected = certificate["selected"]
        print(
            "selected=" + ",".join(selected["channels"])
            + f" cost={selected['weighted_cost']}"
        )
    else:
        witness = certificate["impossibility_witness"]
        print(f"impossible={witness['left']}::{witness['right']}")


def _command_verify(args: argparse.Namespace) -> None:
    model = load_model(args.model)
    certificate = load_json(args.certificate)
    verify_certificate(model, certificate)
    print(f"verified {args.certificate}")


def _command_check(args: argparse.Namespace) -> None:
    certificate, lean_source = _synthesize(args.model)
    if args.certificate.read_bytes() != canonical_bytes(certificate):
        raise SynthesisError(
            f"synthesis certificate drift: regenerate {args.certificate}"
        )
    if args.lean.read_text(encoding="utf-8") != lean_source:
        raise SynthesisError(f"generated Lean drift: regenerate {args.lean}")
    print("generated evidence-synthesis artifacts are reproducible")


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
    except (SynthesisError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
