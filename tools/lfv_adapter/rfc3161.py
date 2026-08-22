from __future__ import annotations

import base64
import re
import shutil
import ssl
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .canonical import hash_bytes, make_document_digest
from .errors import ExecutionError, ValidationError

RFC3161_PROVIDER = "rfc3161"
RFC3161_EVIDENCE_SCHEMA = "lfv-rfc3161-evidence-v1"
RFC3161_TARGET_SCHEMA = "lfv-rfc3161-anchor-target-v1"
MAX_QUERY_BYTES = 64 * 1024
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
_ALLOWED_CONTENT_TYPES = {
    "application/timestamp-reply",
    "application/timestamp-response",
    "application/octet-stream",
}


@dataclass(frozen=True)
class Rfc3161Trust:
    """Verifier-selected trust material for one RFC 3161 token.

    The CA bundle is intentionally supplied outside the evidence bundle. A
    researcher-controlled token cannot make itself trustworthy by embedding its
    own root certificate. The evidence records hashes of these files and the
    verifier checks that the externally selected files match those bindings.
    """

    ca_file: Path
    untrusted_file: Path | None = None
    openssl_binary: str = "openssl"

    def validate(self) -> Rfc3161Trust:
        if not self.openssl_binary:
            raise ValidationError("RFC 3161 OpenSSL binary must be non-empty")
        if (
            shutil.which(self.openssl_binary) is None
            and not Path(self.openssl_binary).is_file()
        ):
            raise ValidationError(f"OpenSSL binary not found: {self.openssl_binary}")
        for label, path in (
            ("CA bundle", self.ca_file),
            ("untrusted bundle", self.untrusted_file),
        ):
            if path is not None and not path.is_file():
                raise ValidationError(f"RFC 3161 {label} is not a file: {path}")
        return self


def anchor_target(
    commitment: dict[str, str], entry_count: int
) -> dict[str, Any]:
    if (
        isinstance(entry_count, bool)
        or not isinstance(entry_count, int)
        or entry_count <= 0
    ):
        raise ValidationError("RFC 3161 anchor target requires a positive entry count")
    return {
        "schema_version": RFC3161_TARGET_SCHEMA,
        "commitment": commitment,
        "entry_count": entry_count,
    }


def anchor_target_digest(
    commitment: dict[str, str], entry_count: int
) -> dict[str, str]:
    """Bind both the terminal commitment and ledger length to a SHA-256 imprint."""

    return make_document_digest(
        domain="rfc3161AnchorTarget",
        schema_id=RFC3161_TARGET_SCHEMA,
        payload=anchor_target(commitment, entry_count),
        algorithm="sha256",
    )


def _run_openssl(
    trust_or_binary: Rfc3161Trust | str,
    args: list[str],
    *,
    data: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    binary = (
        trust_or_binary.openssl_binary
        if isinstance(trust_or_binary, Rfc3161Trust)
        else trust_or_binary
    )
    try:
        result = subprocess.run(
            [binary, *args],
            input=data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ExecutionError(f"failed to execute OpenSSL: {exc}") from exc
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        operation = " ".join(args[:3])
        raise ValidationError(
            f"OpenSSL {operation} failed: {stderr or '<empty stderr>'}"
        )
    return result


def openssl_version(binary: str) -> str:
    return (
        _run_openssl(binary, ["version"])
        .stdout.decode("utf-8", errors="replace")
        .strip()
    )


def create_timestamp_query(
    target_digest: str,
    *,
    openssl_binary: str = "openssl",
    policy_oid: str | None = None,
) -> bytes:
    if not re.fullmatch(r"[0-9a-f]{64}", target_digest):
        raise ValidationError(
            "RFC 3161 target digest must be a SHA-256 lowercase hex string"
        )
    with tempfile.TemporaryDirectory(prefix="lfv-rfc3161-query-") as temporary:
        output = Path(temporary) / "request.tsq"
        arguments = [
            "ts",
            "-query",
            "-digest",
            target_digest,
            "-sha256",
            "-cert",
        ]
        if policy_oid:
            if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)+", policy_oid):
                raise ValidationError("RFC 3161 policy OID is invalid")
            arguments += ["-tspolicy", policy_oid]
        arguments += ["-out", str(output)]
        _run_openssl(openssl_binary, arguments)
        payload = output.read_bytes()
    if not payload or len(payload) > MAX_QUERY_BYTES:
        raise ValidationError("RFC 3161 query size is invalid")
    parsed = parse_timestamp_request(payload, openssl_binary=openssl_binary)
    if (
        parsed["hash_algorithm"] != "sha256"
        or parsed["message_imprint"] != target_digest
    ):
        raise ValidationError(
            "OpenSSL generated an unexpected RFC 3161 request imprint"
        )
    if not parsed["nonce"]:
        raise ValidationError("RFC 3161 query must contain a nonce")
    if not parsed["certificate_required"]:
        raise ValidationError("RFC 3161 query must request the signer certificate")
    return payload


def _decode_text(result: subprocess.CompletedProcess[bytes]) -> str:
    return result.stdout.decode("utf-8", errors="strict")


def _parse_message_imprint(lines: list[str]) -> str:
    collecting = False
    octets: list[str] = []
    for line in lines:
        if line.strip() == "Message data:":
            collecting = True
            continue
        if collecting:
            match = re.match(
                r"^\s*[0-9A-Fa-f]{4}\s*-\s*(.*?)\s{2,}.*$", line
            )
            if not match:
                break
            octets.extend(re.findall(r"[0-9A-Fa-f]{2}", match.group(1)))
    if not octets:
        raise ValidationError(
            "RFC 3161 text output is missing message imprint bytes"
        )
    return "".join(octets).lower()


def _field(
    lines: list[str], prefix: str, *, required: bool = True
) -> str | None:
    for line in lines:
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    if required:
        raise ValidationError(
            f"RFC 3161 text output is missing {prefix.rstrip(':')}"
        )
    return None


def parse_timestamp_request(
    request_der: bytes, *, openssl_binary: str = "openssl"
) -> dict[str, Any]:
    if not request_der or len(request_der) > MAX_QUERY_BYTES:
        raise ValidationError("RFC 3161 query size is invalid")
    with tempfile.TemporaryDirectory(
        prefix="lfv-rfc3161-parse-request-"
    ) as temporary:
        path = Path(temporary) / "request.tsq"
        path.write_bytes(request_der)
        text = _decode_text(
            _run_openssl(
                openssl_binary,
                ["ts", "-query", "-in", str(path), "-text"],
            )
        )
    lines = text.splitlines()
    certificate_required = _field(lines, "Certificate required:")
    return {
        "hash_algorithm": (_field(lines, "Hash Algorithm:") or "").lower(),
        "message_imprint": _parse_message_imprint(lines),
        "policy_oid": _field(lines, "Policy OID:") or "unspecified",
        "nonce": _field(lines, "Nonce:", required=False),
        "certificate_required":
            (certificate_required or "").lower() == "yes",
    }


_TIME_RE = re.compile(
    r"^(?P<month>[A-Z][a-z]{2})\s+(?P<day>\d{1,2})\s+"
    r"(?P<hms>\d{2}:\d{2}:\d{2})(?:\.(?P<fraction>\d+))?\s+"
    r"(?P<year>\d{4})\s+GMT$"
)


def _parse_openssl_time(value: str) -> tuple[str, int, int]:
    match = _TIME_RE.fullmatch(value)
    if not match:
        raise ValidationError(
            f"unsupported RFC 3161 generation time: {value!r}"
        )
    base = datetime.strptime(
        (
            f"{match.group('month')} {match.group('day')} "
            f"{match.group('hms')} {match.group('year')}"
        ),
        "%b %d %H:%M:%S %Y",
    ).replace(tzinfo=timezone.utc)
    fraction = match.group("fraction") or ""
    microseconds = int((fraction + "000000")[:6]) if fraction else 0
    base = base.replace(microsecond=microseconds)
    floor_seconds = int(base.timestamp())
    # Lean's Timestamp is integral. Rounding upward avoids claiming that a
    # fractional timestamp was available earlier than the TSA actually stated.
    ceiling_seconds = floor_seconds + (1 if microseconds else 0)
    timespec = "microseconds" if microseconds else "seconds"
    iso = base.isoformat(timespec=timespec).replace("+00:00", "Z")
    if microseconds:
        iso = iso.replace(
            f".{microseconds:06d}Z", f".{fraction.rstrip('0') or '0'}Z"
        )
    return iso, floor_seconds, ceiling_seconds


def parse_timestamp_response(
    response_der: bytes, *, openssl_binary: str = "openssl"
) -> dict[str, Any]:
    if not response_der or len(response_der) > MAX_RESPONSE_BYTES:
        raise ValidationError("RFC 3161 response size is invalid")
    with tempfile.TemporaryDirectory(
        prefix="lfv-rfc3161-parse-response-"
    ) as temporary:
        path = Path(temporary) / "response.tsr"
        path.write_bytes(response_der)
        text = _decode_text(
            _run_openssl(
                openssl_binary,
                ["ts", "-reply", "-in", str(path), "-text"],
            )
        )
    lines = text.splitlines()
    status = _field(lines, "Status:") or ""
    if not (
        status.startswith("Granted.")
        or status.startswith("Granted with modifications.")
    ):
        raise ValidationError(
            f"RFC 3161 TSA did not grant the request: {status}"
        )
    time_text = _field(lines, "Time stamp:") or ""
    gen_time_utc, floor_seconds, ceiling_seconds = _parse_openssl_time(
        time_text
    )
    return {
        "status": status,
        "hash_algorithm": (_field(lines, "Hash Algorithm:") or "").lower(),
        "message_imprint": _parse_message_imprint(lines),
        "policy_oid": _field(lines, "Policy OID:") or "unspecified",
        "serial_number": _field(lines, "Serial number:") or "",
        "gen_time_utc": gen_time_utc,
        "gen_time_unix_floor": floor_seconds,
        "anchor_time_unix_ceiling": ceiling_seconds,
        "nonce": _field(lines, "Nonce:", required=False),
        "tsa_name": _field(lines, "TSA:", required=False) or "unspecified",
    }


def verify_timestamp_pair(
    request_der: bytes,
    response_der: bytes,
    trust: Rfc3161Trust,
) -> dict[str, Any]:
    trust.validate()
    request = parse_timestamp_request(
        request_der, openssl_binary=trust.openssl_binary
    )
    response = parse_timestamp_response(
        response_der, openssl_binary=trust.openssl_binary
    )
    if not request["certificate_required"]:
        raise ValidationError(
            "RFC 3161 request did not ask the TSA to include its signer certificate"
        )
    if request["hash_algorithm"] != response["hash_algorithm"]:
        raise ValidationError(
            "RFC 3161 request/response hash algorithm mismatch"
        )
    if request["message_imprint"] != response["message_imprint"]:
        raise ValidationError(
            "RFC 3161 request/response message imprint mismatch"
        )
    if not request["nonce"] or request["nonce"] != response["nonce"]:
        raise ValidationError("RFC 3161 request/response nonce mismatch")
    with tempfile.TemporaryDirectory(
        prefix="lfv-rfc3161-verify-"
    ) as temporary:
        request_path = Path(temporary) / "request.tsq"
        response_path = Path(temporary) / "response.tsr"
        request_path.write_bytes(request_der)
        response_path.write_bytes(response_der)
        arguments = [
            "ts",
            "-verify",
            "-queryfile",
            str(request_path),
            "-in",
            str(response_path),
            "-CAfile",
            str(trust.ca_file),
            "-attime",
            str(response["gen_time_unix_floor"]),
            "-purpose",
            "timestampsign",
        ]
        if trust.untrusted_file is not None:
            arguments += ["-untrusted", str(trust.untrusted_file)]
        _run_openssl(trust, arguments)
    return {
        "request": request,
        "response": response,
        "openssl_version": openssl_version(trust.openssl_binary),
    }


def _validate_tsa_url(tsa_url: str, *, allow_http: bool) -> str:
    if not isinstance(tsa_url, str) or not tsa_url:
        raise ValidationError("TSA URL must be a non-empty string")
    parsed = urllib.parse.urlsplit(tsa_url)
    allowed = {"http", "https"} if allow_http else {"https"}
    if parsed.scheme.lower() not in allowed or not parsed.netloc:
        required = "HTTP or HTTPS" if allow_http else "HTTPS"
        raise ValidationError(f"TSA URL must use {required} with a network host")
    if parsed.username or parsed.password:
        raise ValidationError("TSA URL must not embed credentials")
    return tsa_url


class _PolicyRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, allow_http: bool) -> None:
        super().__init__()
        self.allow_http = allow_http

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        scheme = urllib.parse.urlsplit(newurl).scheme.lower()
        allowed = {"http", "https"} if self.allow_http else {"https"}
        if scheme not in allowed:
            raise urllib.error.HTTPError(
                newurl, code, "unsafe timestamp redirect", headers, fp
            )
        return super().redirect_request(
            req, fp, code, msg, headers, newurl
        )


def post_timestamp_query(
    tsa_url: str,
    request_der: bytes,
    *,
    timeout_seconds: int = 30,
    allow_http: bool = False,
    https_ca_file: Path | None = None,
) -> bytes:
    tsa_url = _validate_tsa_url(tsa_url, allow_http=allow_http)
    if timeout_seconds <= 0:
        raise ValidationError("timestamp HTTP timeout must be positive")
    context = ssl.create_default_context(
        cafile=str(https_ca_file) if https_ca_file else None
    )
    opener = urllib.request.build_opener(
        _PolicyRedirectHandler(allow_http),
        urllib.request.HTTPSHandler(context=context),
    )
    request = urllib.request.Request(
        tsa_url,
        data=request_der,
        method="POST",
        headers={
            "Content-Type": "application/timestamp-query",
            "Accept": "application/timestamp-reply",
            "User-Agent": "lean-finance-verification-rfc3161/1",
            "Cache-Control": "no-store",
        },
    )
    try:
        with opener.open(request, timeout=timeout_seconds) as response:
            final_scheme = urllib.parse.urlsplit(
                response.geturl()
            ).scheme.lower()
            allowed = {"http", "https"} if allow_http else {"https"}
            if final_scheme not in allowed:
                raise ExecutionError("TSA redirected to an unsafe URL scheme")
            media_type = (
                response.headers.get("Content-Type", "")
                .split(";", 1)[0]
                .strip()
                .lower()
            )
            if media_type not in _ALLOWED_CONTENT_TYPES:
                raise ExecutionError(
                    "unexpected TSA response content type: "
                    f"{media_type or '<missing>'}"
                )
            payload = response.read(MAX_RESPONSE_BYTES + 1)
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
    ) as exc:
        raise ExecutionError(f"RFC 3161 TSA request failed: {exc}") from exc
    if not payload or len(payload) > MAX_RESPONSE_BYTES:
        raise ExecutionError("RFC 3161 TSA response size is invalid")
    return payload


def _b64encode(payload: bytes) -> str:
    return base64.b64encode(payload).decode("ascii")


def _b64decode(value: Any, *, path: str, maximum: int) -> bytes:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{path}: expected non-empty base64 text")
    try:
        payload = base64.b64decode(value, validate=True)
    except (ValueError, TypeError) as exc:
        raise ValidationError(f"{path}: invalid base64") from exc
    if not payload or len(payload) > maximum:
        raise ValidationError(f"{path}: decoded size is invalid")
    return payload


def _file_sha256(path: Path) -> str:
    if not path.is_file():
        raise ValidationError(f"trust bundle is not a file: {path}")
    return hash_bytes("sha256", path.read_bytes())


def create_rfc3161_anchor(
    ledger: dict[str, Any],
    *,
    tsa_url: str,
    trust: Rfc3161Trust,
    request_der: bytes | None = None,
    response_der: bytes | None = None,
    timeout_seconds: int = 30,
    allow_http: bool = False,
    https_ca_file: Path | None = None,
    policy_oid: str | None = None,
) -> tuple[dict[str, Any], bytes, bytes]:
    """Create or import a signed timestamp for the complete ledger prefix."""

    from .ledger import verify_anchor, verify_ledger

    tsa_url = _validate_tsa_url(tsa_url, allow_http=allow_http)
    verified_ledger = verify_ledger(ledger)
    entries = verified_ledger["entries"]
    if not entries:
        raise ValidationError("cannot timestamp an empty ledger")
    terminal = entries[-1]["commitment"]
    target_ref = anchor_target_digest(terminal, len(entries))
    if request_der is None:
        if response_der is not None:
            raise ValidationError(
                "an offline RFC 3161 response requires its original request"
            )
        request_der = create_timestamp_query(
            target_ref["digest"],
            openssl_binary=trust.openssl_binary,
            policy_oid=policy_oid,
        )
    if response_der is None:
        response_der = post_timestamp_query(
            tsa_url,
            request_der,
            timeout_seconds=timeout_seconds,
            allow_http=allow_http,
            https_ca_file=https_ca_file,
        )
    metadata = verify_timestamp_pair(request_der, response_der, trust)
    request_info = metadata["request"]
    response_info = metadata["response"]
    if request_info["message_imprint"] != target_ref["digest"]:
        raise ValidationError(
            "RFC 3161 query is not bound to the terminal ledger target"
        )
    request_sha256 = hash_bytes("sha256", request_der)
    response_sha256 = hash_bytes("sha256", response_der)
    ca_sha256 = _file_sha256(trust.ca_file)
    untrusted_sha256 = (
        _file_sha256(trust.untrusted_file)
        if trust.untrusted_file is not None
        else None
    )
    anchor = {
        "schema_version": "lfv-ledger-anchor-v1",
        "canonical_format": "lfv-canonical-json-v1",
        "commitment": terminal,
        "entry_count": len(entries),
        "anchored_at": response_info["anchor_time_unix_ceiling"],
        "provider": RFC3161_PROVIDER,
        "evidence_id": f"rfc3161:sha256:{response_sha256}",
        "evidence": {
            "schema_version": RFC3161_EVIDENCE_SCHEMA,
            "tsa_url": tsa_url,
            "target": target_ref,
            "request_der_base64": _b64encode(request_der),
            "response_der_base64": _b64encode(response_der),
            "request_sha256": request_sha256,
            "response_sha256": response_sha256,
            "hash_algorithm": response_info["hash_algorithm"],
            "message_imprint": response_info["message_imprint"],
            "policy_oid": response_info["policy_oid"],
            "serial_number": response_info["serial_number"],
            "nonce": response_info["nonce"],
            "tsa_name": response_info["tsa_name"],
            "gen_time_utc": response_info["gen_time_utc"],
            "gen_time_unix_floor": response_info["gen_time_unix_floor"],
            "anchor_time_unix_ceiling":
                response_info["anchor_time_unix_ceiling"],
            "ca_bundle_sha256": ca_sha256,
            "untrusted_bundle_sha256": untrusted_sha256,
            "openssl_version": metadata["openssl_version"],
        },
    }
    verified_anchor = verify_anchor(
        anchor,
        verified_ledger,
        rfc3161_trust=trust,
    )
    return verified_anchor, request_der, response_der


def verify_rfc3161_anchor_evidence(
    anchor: dict[str, Any],
    *,
    trust: Rfc3161Trust | None,
) -> dict[str, Any]:
    if trust is None:
        raise ValidationError(
            "RFC 3161 anchor requires an external CA trust bundle "
            "for verification"
        )
    trust.validate()
    evidence = anchor.get("evidence")
    if not isinstance(evidence, dict):
        raise ValidationError(
            "anchor.evidence: RFC 3161 evidence object is required"
        )
    expected = {
        "schema_version",
        "tsa_url",
        "target",
        "request_der_base64",
        "response_der_base64",
        "request_sha256",
        "response_sha256",
        "hash_algorithm",
        "message_imprint",
        "policy_oid",
        "serial_number",
        "nonce",
        "tsa_name",
        "gen_time_utc",
        "gen_time_unix_floor",
        "anchor_time_unix_ceiling",
        "ca_bundle_sha256",
        "untrusted_bundle_sha256",
        "openssl_version",
    }
    unknown = set(evidence) - expected
    missing = expected - set(evidence)
    if unknown:
        raise ValidationError(
            f"anchor.evidence: unknown fields: {sorted(unknown)}"
        )
    if missing:
        raise ValidationError(
            f"anchor.evidence: missing fields: {sorted(missing)}"
        )
    if evidence["schema_version"] != RFC3161_EVIDENCE_SCHEMA:
        raise ValidationError(
            "anchor.evidence.schema_version: unexpected value"
        )
    _validate_tsa_url(evidence["tsa_url"], allow_http=True)
    target_ref = anchor_target_digest(
        anchor["commitment"], anchor["entry_count"]
    )
    if evidence["target"] != target_ref:
        raise ValidationError(
            "anchor.evidence.target: terminal ledger binding mismatch"
        )
    request_der = _b64decode(
        evidence["request_der_base64"],
        path="anchor.evidence.request_der_base64",
        maximum=MAX_QUERY_BYTES,
    )
    response_der = _b64decode(
        evidence["response_der_base64"],
        path="anchor.evidence.response_der_base64",
        maximum=MAX_RESPONSE_BYTES,
    )
    request_sha256 = hash_bytes("sha256", request_der)
    response_sha256 = hash_bytes("sha256", response_der)
    if evidence["request_sha256"] != request_sha256:
        raise ValidationError(
            "anchor.evidence.request_sha256: DER digest mismatch"
        )
    if evidence["response_sha256"] != response_sha256:
        raise ValidationError(
            "anchor.evidence.response_sha256: DER digest mismatch"
        )
    if anchor["evidence_id"] != f"rfc3161:sha256:{response_sha256}":
        raise ValidationError(
            "anchor.evidence_id: RFC 3161 response identity mismatch"
        )
    if evidence["ca_bundle_sha256"] != _file_sha256(trust.ca_file):
        raise ValidationError(
            "RFC 3161 CA bundle does not match the evidence binding"
        )
    expected_untrusted = (
        _file_sha256(trust.untrusted_file)
        if trust.untrusted_file is not None
        else None
    )
    if evidence["untrusted_bundle_sha256"] != expected_untrusted:
        raise ValidationError(
            "RFC 3161 untrusted certificate bundle mismatch"
        )
    metadata = verify_timestamp_pair(request_der, response_der, trust)
    request_info = metadata["request"]
    response_info = metadata["response"]
    if request_info["message_imprint"] != target_ref["digest"]:
        raise ValidationError(
            "RFC 3161 request does not bind the terminal ledger target"
        )
    comparisons = {
        "hash_algorithm": response_info["hash_algorithm"],
        "message_imprint": response_info["message_imprint"],
        "policy_oid": response_info["policy_oid"],
        "serial_number": response_info["serial_number"],
        "nonce": response_info["nonce"],
        "tsa_name": response_info["tsa_name"],
        "gen_time_utc": response_info["gen_time_utc"],
        "gen_time_unix_floor": response_info["gen_time_unix_floor"],
        "anchor_time_unix_ceiling":
            response_info["anchor_time_unix_ceiling"],
    }
    for field, expected_value in comparisons.items():
        if evidence[field] != expected_value:
            raise ValidationError(
                f"anchor.evidence.{field}: parsed token value mismatch"
            )
    if anchor["anchored_at"] != response_info["anchor_time_unix_ceiling"]:
        raise ValidationError(
            "anchor.anchored_at must conservatively round RFC 3161 time upward"
        )
    if not isinstance(evidence["openssl_version"], str) or not evidence[
        "openssl_version"
    ]:
        raise ValidationError(
            "anchor.evidence.openssl_version must be non-empty"
        )
    return evidence
