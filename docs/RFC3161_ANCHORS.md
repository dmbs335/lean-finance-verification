# RFC 3161 Ledger Anchors

A committed search ledger prevents silent edits inside one declared history, but a researcher could still construct that entire history after observing the backtest result. An external timestamp closes that gap by proving that a commitment to the complete ledger prefix existed no later than a trusted time.

The reference adapter supports RFC 3161 Time-Stamp Protocol responses as one external anchor mechanism.

## What is timestamped

The TSA does not timestamp the ledger JSON directly. It timestamps a SHA-256 digest of a domain-separated canonical object:

```text
{
  "schema_version": "lfv-rfc3161-anchor-target-v1",
  "commitment": <terminal search-ledger ArtifactRef>,
  "entry_count": <number of committed trials>
}
```

The target digest is computed as:

```text
LFV\0ARTIFACT\0V1\0rfc3161AnchorTarget\0
lfv-rfc3161-anchor-target-v1\0
<canonical-json-bytes>
```

Binding both the terminal commitment and the entry count prevents a timestamp for one prefix from being reinterpreted as evidence for a different-length ledger.

## Online issuance

The normal command posts an RFC 3161 query to an HTTPS TSA, verifies the returned token immediately, and writes a canonical anchor containing the original DER request and response.

```bash
python -m tools.lfv_adapter make-rfc3161-anchor \
  --ledger research/search-ledger.json \
  --tsa-url https://tsa.example.org/ \
  --rfc3161-ca-file trust/tsa-roots.pem \
  --rfc3161-untrusted-file trust/tsa-intermediates.pem \
  --out research/ledger-anchor.json \
  --request-out research/ledger-anchor.tsq \
  --response-out research/ledger-anchor.tsr \
  --pretty
```

`--rfc3161-ca-file` is the trust bundle used to validate the TSA signing certificate. It is selected by the verifier and is deliberately not taken from the timestamp evidence itself.

`--https-ca-file`, when supplied, controls TLS server-certificate validation for the HTTP connection. It is separate from the TSA signing-certificate trust bundle. A TLS connection can be valid while the timestamp signature is untrusted, and vice versa.

Plain HTTP is rejected by default. `--allow-http` exists only for isolated test fixtures.

## Offline or separately transported response

An original request and its response can be imported without contacting the TSA again:

```bash
python -m tools.lfv_adapter make-rfc3161-anchor \
  --ledger research/search-ledger.json \
  --tsa-url https://tsa.example.org/ \
  --request-file research/ledger-anchor.tsq \
  --response-file research/ledger-anchor.tsr \
  --rfc3161-ca-file trust/tsa-roots.pem \
  --rfc3161-untrusted-file trust/tsa-intermediates.pem \
  --out research/ledger-anchor.json
```

The request must be the exact query answered by the response. The adapter checks the nonce and message imprint rather than accepting an unrelated token for the same nominal provider.

## Verification during build

A bundle containing an RFC 3161 anchor is rejected unless the verifier provides the bound trust material:

```bash
python -m tools.lfv_adapter build \
  --spec research/experiment.json \
  --out research/generated \
  --rfc3161-ca-file trust/tsa-roots.pem \
  --rfc3161-untrusted-file trust/tsa-intermediates.pem

python -m tools.lfv_adapter verify \
  --bundle research/generated/bundle.canonical.json \
  --rfc3161-ca-file trust/tsa-roots.pem \
  --rfc3161-untrusted-file trust/tsa-intermediates.pem
```

The evidence records SHA-256 hashes of both trust files. Supplying a different root or intermediate bundle is therefore detected before the token is accepted.

## Checks performed

The adapter performs all of the following before constructing a usable anchor:

1. parses the original request and requires a nonce and included-signer-certificate request;
2. requires a granted RFC 3161 response status;
3. checks that request and response use the same hash algorithm, message imprint, and nonce;
4. checks that the imprint equals the domain-separated terminal-ledger target;
5. verifies the timestamp signature and signer chain using verifier-selected trust material;
6. verifies the certificate for timestamp-signing usage at the token generation time;
7. binds the complete DER request and response by SHA-256 in the evidence object;
8. binds the evidence identifier to the response DER digest;
9. re-parses the token on every bundle verification and compares all recorded metadata;
10. requires the conservatively rounded timestamp to be no later than the research decision cutoff.

The adapter delegates ASN.1, CMS signature, and X.509 path validation to the selected OpenSSL executable. The OpenSSL version is recorded for reproducibility but is not itself a trust guarantee.

## Timestamp units and fractional seconds

The existing Lean model represents `Timestamp` as a natural number. Production RFC 3161 workflows must therefore represent decision times, registration times, and availability times as Unix seconds.

An RFC 3161 `genTime` may contain fractional seconds. The evidence stores both:

- `gen_time_unix_floor`: the integral second used for certificate validity checking; and
- `anchor_time_unix_ceiling`: the timestamp used by the formal cutoff contract.

The formal anchor time is rounded upward whenever a fractional component is present. This avoids claiming that evidence was available before the TSA-stated instant.

## Evidence object

An RFC 3161 anchor has `provider = "rfc3161"` and includes:

- base64-encoded DER request and response;
- SHA-256 hashes of both DER objects;
- target digest, message imprint, nonce, policy, serial number, TSA name, and generation time;
- verifier-selected CA and optional intermediate-bundle hashes;
- the OpenSSL version used by the adapter.

The corresponding interoperability schema is:

```text
schemas/lfv-ledger-anchor-v1.schema.json
```

## Remaining trust boundary

This implementation materially strengthens the earlier local anchor, but it does not eliminate all external assumptions.

It does not prove:

- that the selected TSA was independent of the researcher;
- that the CA trust bundle was distributed correctly;
- that a compromised TSA did not backdate or equivocate;
- that the local operating system, OpenSSL binary, or wall clock was uncompromised;
- certificate revocation status through OCSP or CRLs;
- long-term validity after the signing algorithms or TSA certificate expire.

For higher-assurance archival use, preserve the DER request and response, the exact trust material, revocation evidence, and a second independent transparency-log or timestamp anchor. The formal layer can then require multiple independent anchor witnesses rather than relying on one provider.
