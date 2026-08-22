from __future__ import annotations

import base64
import copy
import shutil
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from tools.lfv_adapter.canonical import hash_bytes, make_artifact_ref
from tools.lfv_adapter.errors import ValidationError
from tools.lfv_adapter.ledger import (
    append_trial,
    empty_ledger,
    verify_anchor,
)
from tools.lfv_adapter.rfc3161 import (
    Rfc3161Trust,
    anchor_target_digest,
    create_rfc3161_anchor,
    create_timestamp_query,
    post_timestamp_query,
)


@unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required")
class Rfc3161Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary = tempfile.TemporaryDirectory(
            prefix="lfv-rfc3161-tests-"
        )
        cls.root = Path(cls._temporary.name)
        cls.openssl = shutil.which("openssl") or "openssl"
        cls.root_key = cls.root / "root.key"
        cls.root_cert = cls.root / "root.crt"
        cls.tsa_key = cls.root / "tsa.key"
        cls.tsa_csr = cls.root / "tsa.csr"
        cls.tsa_cert = cls.root / "tsa.crt"
        cls.serial = cls.root / "tsa-serial"
        cls.tsa_config = cls.root / "tsa.cnf"
        cls._build_test_pki()
        cls.trust = Rfc3161Trust(
            ca_file=cls.root_cert,
            openssl_binary=cls.openssl,
        ).validate()
        code, _ = make_artifact_ref(
            kind="sourceCode",
            schema_id="test-code-v1",
            payload={"code": "return 1"},
            algorithm="sha256",
        )
        parameters, _ = make_artifact_ref(
            kind="parameterSet",
            schema_id="test-parameters-v1",
            payload={"lookback": 1},
            algorithm="sha256",
        )
        cls.ledger = append_trial(
            empty_ledger(),
            hypothesis_id="rfc3161-test",
            parameters=parameters,
            code=code,
            registered_at=1,
            algorithm="sha256",
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary.cleanup()

    @classmethod
    def _run(cls, arguments: list[str]) -> subprocess.CompletedProcess[bytes]:
        completed = subprocess.run(
            [cls.openssl, *arguments],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
        if completed.returncode != 0:
            raise AssertionError(
                completed.stderr.decode("utf-8", errors="replace")
            )
        return completed

    @classmethod
    def _build_test_pki(cls) -> None:
        cls._run(
            [
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-keyout",
                str(cls.root_key),
                "-out",
                str(cls.root_cert),
                "-subj",
                "/CN=LFV RFC3161 Test Root",
                "-days",
                "2",
                "-sha256",
                "-addext",
                "basicConstraints=critical,CA:TRUE",
                "-addext",
                "keyUsage=critical,keyCertSign,cRLSign",
            ]
        )
        cls._run(
            [
                "req",
                "-new",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-keyout",
                str(cls.tsa_key),
                "-out",
                str(cls.tsa_csr),
                "-subj",
                "/CN=LFV RFC3161 Test TSA",
                "-sha256",
            ]
        )
        extension_file = cls.root / "tsa-ext.cnf"
        extension_file.write_text(
            """[tsa_cert]
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature
extendedKeyUsage=critical,timeStamping
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid,issuer
""",
            encoding="utf-8",
        )
        cls._run(
            [
                "x509",
                "-req",
                "-in",
                str(cls.tsa_csr),
                "-CA",
                str(cls.root_cert),
                "-CAkey",
                str(cls.root_key),
                "-CAcreateserial",
                "-out",
                str(cls.tsa_cert),
                "-days",
                "2",
                "-sha256",
                "-extfile",
                str(extension_file),
                "-extensions",
                "tsa_cert",
            ]
        )
        cls.serial.write_text("01\n", encoding="ascii")
        cls.tsa_config.write_text(
            f"""[ tsa ]
default_tsa = tsa_config1

[ tsa_config1 ]
serial = {cls.serial}
signer_cert = {cls.tsa_cert}
certs = {cls.root_cert}
signer_key = {cls.tsa_key}
signer_digest = sha256
default_policy = 1.2.3.4.1
other_policies = 1.2.3.4.2
digests = sha256, sha384, sha512
accuracy = secs:1, millisecs:500, microsecs:100
clock_precision_digits = 3
ordering = yes
tsa_name = yes
ess_cert_id_chain = yes
ess_cert_id_alg = sha256
""",
            encoding="utf-8",
        )

    @classmethod
    def _issue_response(cls, request_der: bytes) -> bytes:
        with tempfile.TemporaryDirectory(
            dir=cls.root, prefix="issued-"
        ) as temporary:
            query = Path(temporary) / "request.tsq"
            response = Path(temporary) / "response.tsr"
            query.write_bytes(request_der)
            cls._run(
                [
                    "ts",
                    "-reply",
                    "-config",
                    str(cls.tsa_config),
                    "-section",
                    "tsa_config1",
                    "-queryfile",
                    str(query),
                    "-out",
                    str(response),
                ]
            )
            return response.read_bytes()

    @classmethod
    def _offline_anchor(cls) -> dict[str, Any]:
        terminal = cls.ledger["entries"][-1]["commitment"]
        target = anchor_target_digest(terminal, len(cls.ledger["entries"]))
        request_der = create_timestamp_query(
            target["digest"], openssl_binary=cls.openssl
        )
        response_der = cls._issue_response(request_der)
        anchor, _, _ = create_rfc3161_anchor(
            cls.ledger,
            tsa_url="https://tsa.example.test/rfc3161",
            trust=cls.trust,
            request_der=request_der,
            response_der=response_der,
        )
        return anchor

    def test_signed_anchor_verifies_against_external_trust(self) -> None:
        anchor = self._offline_anchor()
        verified = verify_anchor(
            anchor,
            self.ledger,
            cutoff_time=anchor["anchored_at"] + 1,
            rfc3161_trust=self.trust,
        )
        self.assertEqual(verified["provider"], "rfc3161")
        self.assertEqual(
            verified["evidence"]["message_imprint"],
            verified["evidence"]["target"]["digest"],
        )
        self.assertTrue(verified["evidence"]["nonce"])

    def test_rfc3161_anchor_requires_verifier_selected_trust(self) -> None:
        anchor = self._offline_anchor()
        with self.assertRaisesRegex(ValidationError, "external CA trust"):
            verify_anchor(anchor, self.ledger)

    def test_ca_bundle_substitution_is_rejected(self) -> None:
        anchor = self._offline_anchor()
        wrong_key = self.root / "wrong-root.key"
        wrong_cert = self.root / "wrong-root.crt"
        self._run(
            [
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-keyout",
                str(wrong_key),
                "-out",
                str(wrong_cert),
                "-subj",
                "/CN=Wrong RFC3161 Root",
                "-days",
                "2",
                "-sha256",
            ]
        )
        wrong_trust = Rfc3161Trust(
            ca_file=wrong_cert, openssl_binary=self.openssl
        )
        with self.assertRaisesRegex(ValidationError, "CA bundle"):
            verify_anchor(
                anchor,
                self.ledger,
                rfc3161_trust=wrong_trust,
            )

    def test_tampered_timestamp_response_is_rejected(self) -> None:
        anchor = copy.deepcopy(self._offline_anchor())
        response = bytearray(
            base64.b64decode(
                anchor["evidence"]["response_der_base64"], validate=True
            )
        )
        response[-1] ^= 1
        response_bytes = bytes(response)
        response_sha256 = hash_bytes("sha256", response_bytes)
        anchor["evidence"]["response_der_base64"] = base64.b64encode(
            response_bytes
        ).decode("ascii")
        anchor["evidence"]["response_sha256"] = response_sha256
        anchor["evidence_id"] = f"rfc3161:sha256:{response_sha256}"
        with self.assertRaises(ValidationError):
            verify_anchor(
                anchor,
                self.ledger,
                rfc3161_trust=self.trust,
            )

    def test_http_transport_is_opt_in_and_response_is_verified(self) -> None:
        test_case = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802 - HTTP handler API
                length = int(self.headers.get("Content-Length", "0"))
                request_der = self.rfile.read(length)
                response_der = test_case._issue_response(request_der)
                self.send_response(200)
                self.send_header(
                    "Content-Type", "application/timestamp-reply"
                )
                self.send_header("Content-Length", str(len(response_der)))
                self.end_headers()
                self.wfile.write(response_der)

            def log_message(self, format: str, *args: object) -> None:
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            tsa_url = f"http://127.0.0.1:{server.server_port}/timestamp"
            with self.assertRaisesRegex(ValidationError, "HTTPS"):
                post_timestamp_query(tsa_url, b"not-sent")
            anchor, _, _ = create_rfc3161_anchor(
                self.ledger,
                tsa_url=tsa_url,
                trust=self.trust,
                allow_http=True,
            )
            self.assertEqual(anchor["provider"], "rfc3161")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
