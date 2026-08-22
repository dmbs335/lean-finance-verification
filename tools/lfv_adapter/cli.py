from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .bundle import (
    build_from_spec,
    compute_preregistration_artifacts,
    verify_bundle,
    write_build_result,
)
from .canonical import (
    canonical_bytes,
    load_json,
    write_canonical_json,
    write_pretty_json,
)
from .errors import AdapterError, ValidationError
from .ledger import append_trial, load_ledger, make_local_anchor
from .rfc3161 import Rfc3161Trust, create_rfc3161_anchor
from .spec import load_experiment_spec


def _path(value: str) -> Path:
    return Path(value)


def _add_local_anchor_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--allow-local-anchor",
        action="store_true",
        help=(
            "accept provider=local-development; fixtures only, never "
            "external evidence"
        ),
    )


def _add_rfc3161_trust_flags(
    parser: argparse.ArgumentParser, *, required: bool = False
) -> None:
    parser.add_argument(
        "--rfc3161-ca-file",
        type=_path,
        required=required,
        help="verifier-selected PEM trust bundle for the TSA certificate chain",
    )
    parser.add_argument(
        "--rfc3161-untrusted-file",
        type=_path,
        help="optional PEM bundle of intermediate certificates",
    )
    parser.add_argument(
        "--rfc3161-openssl",
        default="openssl",
        help="OpenSSL executable used for RFC 3161 parsing and verification",
    )


def _rfc3161_trust_from_args(
    args: argparse.Namespace, *, required: bool = False
) -> Rfc3161Trust | None:
    ca_file = getattr(args, "rfc3161_ca_file", None)
    untrusted_file = getattr(args, "rfc3161_untrusted_file", None)
    openssl_binary = getattr(args, "rfc3161_openssl", "openssl")
    if ca_file is None:
        if untrusted_file is not None:
            raise ValidationError(
                "--rfc3161-untrusted-file requires --rfc3161-ca-file"
            )
        if required:
            raise ValidationError("--rfc3161-ca-file is required")
        return None
    return Rfc3161Trust(
        ca_file=ca_file,
        untrusted_file=untrusted_file,
        openssl_binary=openssl_binary,
    ).validate()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lfv-adapter",
        description="Reference empirical adapter for proof-carrying backtests",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    preregister = subparsers.add_parser(
        "preregister",
        help="append a code/parameter trial to a committed search ledger",
    )
    preregister.add_argument("--spec", required=True, type=_path)
    preregister.add_argument("--registered-at", required=True, type=int)
    preregister.add_argument(
        "--ledger",
        type=_path,
        help="output ledger path; defaults to ledger_path relative to the spec",
    )
    preregister.add_argument("--pretty", action="store_true")

    local_anchor = subparsers.add_parser(
        "make-local-anchor",
        help=(
            "create structurally valid local fixture evidence "
            "(not an external timestamp)"
        ),
    )
    local_anchor.add_argument("--ledger", required=True, type=_path)
    local_anchor.add_argument("--anchored-at", required=True, type=int)
    local_anchor.add_argument("--out", required=True, type=_path)
    local_anchor.add_argument("--pretty", action="store_true")

    rfc3161_anchor = subparsers.add_parser(
        "make-rfc3161-anchor",
        help=(
            "timestamp the complete ledger prefix with an RFC 3161 TSA and "
            "write self-contained DER evidence"
        ),
    )
    rfc3161_anchor.add_argument("--ledger", required=True, type=_path)
    rfc3161_anchor.add_argument("--tsa-url", required=True)
    rfc3161_anchor.add_argument("--out", required=True, type=_path)
    rfc3161_anchor.add_argument(
        "--request-file",
        type=_path,
        help="original DER request when importing an offline TSA response",
    )
    rfc3161_anchor.add_argument(
        "--response-file",
        type=_path,
        help="DER response obtained out of band; requires --request-file",
    )
    rfc3161_anchor.add_argument(
        "--request-out",
        type=_path,
        help="also persist the DER request used for this anchor",
    )
    rfc3161_anchor.add_argument(
        "--response-out",
        type=_path,
        help="also persist the DER TSA response",
    )
    rfc3161_anchor.add_argument(
        "--timeout-seconds", type=int, default=30
    )
    rfc3161_anchor.add_argument(
        "--https-ca-file",
        type=_path,
        help="optional CA bundle for the HTTPS transport connection",
    )
    rfc3161_anchor.add_argument(
        "--policy-oid",
        help="optional numeric TSA policy OID requested in the timestamp query",
    )
    rfc3161_anchor.add_argument(
        "--allow-http",
        action="store_true",
        help="permit plaintext HTTP; intended only for isolated test fixtures",
    )
    rfc3161_anchor.add_argument("--pretty", action="store_true")
    _add_rfc3161_trust_flags(rfc3161_anchor, required=True)

    build = subparsers.add_parser(
        "build",
        help="execute an experiment and emit canonical JSON plus Lean source",
    )
    build.add_argument("--spec", required=True, type=_path)
    build.add_argument("--out", required=True, type=_path)
    build.add_argument(
        "--lean-out",
        type=_path,
        help="also write the generated Lean module to this repository path",
    )
    _add_local_anchor_flag(build)
    _add_rfc3161_trust_flags(build)

    verify = subparsers.add_parser(
        "verify", help="verify a canonical adapter bundle"
    )
    verify.add_argument("--bundle", required=True, type=_path)
    _add_local_anchor_flag(verify)
    _add_rfc3161_trust_flags(verify)

    check = subparsers.add_parser(
        "check-generated",
        help=(
            "rebuild a fixture and fail if checked-in canonical JSON or "
            "Lean source drifted"
        ),
    )
    check.add_argument("--spec", required=True, type=_path)
    check.add_argument("--bundle", required=True, type=_path)
    check.add_argument("--lean", required=True, type=_path)
    _add_local_anchor_flag(check)
    _add_rfc3161_trust_flags(check)
    return parser


def _command_preregister(args: argparse.Namespace) -> None:
    if args.registered_at < 0:
        raise ValidationError("registered-at must be non-negative")
    spec = load_experiment_spec(args.spec)
    code, parameters = compute_preregistration_artifacts(spec)
    ledger_path = args.ledger or spec.resolve(
        spec.ledger_path, must_exist=False
    )
    ledger = load_ledger(ledger_path, allow_missing=True)
    updated = append_trial(
        ledger,
        hypothesis_id=spec.decision.strategy_id,
        parameters=parameters,
        code=code,
        registered_at=args.registered_at,
        algorithm=spec.hash_algorithm,
    )
    write_canonical_json(ledger_path, updated)
    if args.pretty:
        write_pretty_json(
            ledger_path.with_suffix(".pretty.json"), updated
        )
    print(f"wrote {ledger_path}")
    print(updated["entries"][-1]["commitment"]["digest"])


def _command_local_anchor(args: argparse.Namespace) -> None:
    if args.anchored_at < 0:
        raise ValidationError("anchored-at must be non-negative")
    ledger = load_ledger(args.ledger)
    anchor = make_local_anchor(ledger, anchored_at=args.anchored_at)
    write_canonical_json(args.out, anchor)
    if args.pretty:
        write_pretty_json(args.out.with_suffix(".pretty.json"), anchor)
    print(f"wrote {args.out}")
    print(
        "warning: local-development anchors are fixtures, not external "
        "timestamp evidence"
    )


def _command_rfc3161_anchor(args: argparse.Namespace) -> None:
    trust = _rfc3161_trust_from_args(args, required=True)
    assert trust is not None
    if (args.request_file is None) != (args.response_file is None):
        raise ValidationError(
            "--request-file and --response-file must be supplied together"
        )
    request_der = (
        args.request_file.read_bytes()
        if args.request_file is not None
        else None
    )
    response_der = (
        args.response_file.read_bytes()
        if args.response_file is not None
        else None
    )
    ledger = load_ledger(args.ledger)
    anchor, request_der, response_der = create_rfc3161_anchor(
        ledger,
        tsa_url=args.tsa_url,
        trust=trust,
        request_der=request_der,
        response_der=response_der,
        timeout_seconds=args.timeout_seconds,
        allow_http=args.allow_http,
        https_ca_file=args.https_ca_file,
        policy_oid=args.policy_oid,
    )
    write_canonical_json(args.out, anchor)
    if args.pretty:
        write_pretty_json(args.out.with_suffix(".pretty.json"), anchor)
    for path, payload in (
        (args.request_out, request_der),
        (args.response_out, response_der),
    ):
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
    print(f"wrote {args.out}")
    print(anchor["evidence_id"])
    print(anchor["evidence"]["gen_time_utc"])


def _command_build(args: argparse.Namespace) -> None:
    trust = _rfc3161_trust_from_args(args)
    result = build_from_spec(
        args.spec,
        allow_local_anchor=args.allow_local_anchor,
        rfc3161_trust=trust,
    )
    write_build_result(result, args.out)
    if args.lean_out:
        args.lean_out.parent.mkdir(parents=True, exist_ok=True)
        args.lean_out.write_text(result.lean_source, encoding="utf-8")
    print(
        f"wrote canonical bundle and generated Lean source to {args.out}"
    )


def _command_verify(args: argparse.Namespace) -> None:
    trust = _rfc3161_trust_from_args(args)
    bundle = load_json(args.bundle)
    verify_bundle(
        bundle,
        allow_local_anchor=args.allow_local_anchor,
        rfc3161_trust=trust,
    )
    print(f"verified {args.bundle}")


def _command_check(args: argparse.Namespace) -> None:
    trust = _rfc3161_trust_from_args(args)
    result = build_from_spec(
        args.spec,
        allow_local_anchor=args.allow_local_anchor,
        rfc3161_trust=trust,
    )
    expected_bundle = args.bundle.read_bytes()
    actual_bundle = canonical_bytes(result.bundle)
    if expected_bundle != actual_bundle:
        raise ValidationError(
            f"canonical bundle drift: regenerate {args.bundle} with the "
            "build command"
        )
    expected_lean = args.lean.read_text(encoding="utf-8")
    if expected_lean != result.lean_source:
        raise ValidationError(
            f"generated Lean drift: regenerate {args.lean}"
        )
    print("generated artifacts are reproducible")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "preregister":
            _command_preregister(args)
        elif args.command == "make-local-anchor":
            _command_local_anchor(args)
        elif args.command == "make-rfc3161-anchor":
            _command_rfc3161_anchor(args)
        elif args.command == "build":
            _command_build(args)
        elif args.command == "verify":
            _command_verify(args)
        elif args.command == "check-generated":
            _command_check(args)
        else:  # pragma: no cover - argparse prevents this branch.
            parser.error(f"unknown command: {args.command}")
        return 0
    except (AdapterError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
