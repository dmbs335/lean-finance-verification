from __future__ import annotations

import base64
import hashlib
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError


def public_key_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sign(payload: dict[str, Any], private_key: Path, *, openssl: str = "openssl") -> str:
    with tempfile.TemporaryDirectory(prefix="lfv-vendor-sign-") as temporary:
        message = Path(temporary) / "manifest.json"
        signature = Path(temporary) / "manifest.sig"
        message.write_bytes(canonical_bytes(payload))
        completed = subprocess.run(
            [openssl, "dgst", "-sha256", "-sign", str(private_key),
             "-out", str(signature), str(message)],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False, timeout=30,
        )
        if completed.returncode != 0:
            raise ValidationError(completed.stderr.decode("utf-8", errors="replace"))
        return base64.b64encode(signature.read_bytes()).decode("ascii")


def verify(payload: dict[str, Any], signature_base64: str, public_key: Path,
           *, openssl: str = "openssl") -> None:
    try:
        signature_bytes = base64.b64decode(signature_base64, validate=True)
    except (TypeError, ValueError) as exc:
        raise ValidationError("manifest signature is not valid base64") from exc
    with tempfile.TemporaryDirectory(prefix="lfv-vendor-verify-") as temporary:
        message = Path(temporary) / "manifest.json"
        signature = Path(temporary) / "manifest.sig"
        message.write_bytes(canonical_bytes(payload))
        signature.write_bytes(signature_bytes)
        completed = subprocess.run(
            [openssl, "dgst", "-sha256", "-verify", str(public_key),
             "-signature", str(signature), str(message)],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False, timeout=30,
        )
        if completed.returncode != 0:
            raise ValidationError("vendor manifest signature verification failed")
