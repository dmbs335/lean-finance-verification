# Python Reference Adapter

`tools/lfv_adapter` is the executable boundary between an empirical backtest and the Lean contracts in `LeanFinance/Backtest`.

It performs five operations in one deterministic pipeline:

1. hashes source files, datasets, parameters, and the declared environment;
2. verifies a commitment-chained search ledger and its pre-decision anchor;
3. executes the empirical command without a shell and requires canonicalizable JSON output;
4. checks point-in-time data and transitive feature-lineage ordering;
5. emits a canonical certificate bundle and a concrete Lean `CertifiedAdapterOutput` witness.

The adapter does not prove profitability, data truth, or model correctness. Anchor authenticity depends on the configured provider and verifier-selected trust material.

## Canonical JSON v1

`lfv-canonical-json-v1` is intentionally narrower than general JSON:

- values may be null, booleans, integers, strings, arrays, or string-keyed objects;
- floating-point numbers are rejected;
- text is encoded as UTF-8;
- object keys are sorted;
- separators are exactly `,` and `:` with no insignificant whitespace;
- canonical bytes have no trailing newline.

Artifact digests are domain separated before hashing:

```text
LFV\0ARTIFACT\0V1\0<artifact-kind>\0<schema-id>\0<canonical-json-bytes>
```

Consequently, equal payloads used as a dataset and a result do not receive the same artifact identity. SHA-256 and SHA-512 use the Python standard library. BLAKE3 is accepted only when the optional `blake3` package is installed.

Source-code artifacts use UTF-8 with every CRLF or CR line ending normalized
to LF before size and digest computation. Dataset artifacts remain byte-exact.
This keeps registered source identity stable across Windows and Unix checkouts
without changing the evidentiary meaning of raw input data.

## Reference fixture flow

From the repository root:

```bash
python -m tools.lfv_adapter preregister \
  --spec examples/reference_adapter/experiment.json \
  --registered-at 7

python -m tools.lfv_adapter make-local-anchor \
  --ledger examples/reference_adapter/ledger.json \
  --anchored-at 8 \
  --out examples/reference_adapter/anchor.json

python -m tools.lfv_adapter build \
  --spec examples/reference_adapter/experiment.json \
  --out /tmp/lfv-reference \
  --lean-out LeanFinance/Generated/ReferenceAdapter.lean \
  --allow-local-anchor
```

`make-local-anchor` is only a fixture utility. It proves that the anchor structurally binds the terminal ledger commitment and entry count, but it is not external timestamp evidence. It is rejected unless `--allow-local-anchor` is explicitly supplied.

## Production RFC 3161 flow

A production ledger can be anchored with a signed RFC 3161 timestamp response:

```bash
python -m tools.lfv_adapter make-rfc3161-anchor \
  --ledger research/search-ledger.json \
  --tsa-url https://tsa.example.org/ \
  --rfc3161-ca-file trust/tsa-roots.pem \
  --rfc3161-untrusted-file trust/tsa-intermediates.pem \
  --out research/ledger-anchor.json \
  --request-out research/ledger-anchor.tsq \
  --response-out research/ledger-anchor.tsr
```

The adapter re-verifies the request nonce, message imprint, CMS signature, timestamp-signing certificate chain, TSA generation time, terminal ledger commitment, and entry count whenever the anchor is used. The trust bundle is supplied by the verifier rather than accepted from the evidence object.

A bundle containing this anchor must be built and verified with the same bound trust material:

```bash
python -m tools.lfv_adapter build \
  --spec research/experiment.json \
  --out research/generated \
  --rfc3161-ca-file trust/tsa-roots.pem \
  --rfc3161-untrusted-file trust/tsa-intermediates.pem
```

See [`RFC3161_ANCHORS.md`](RFC3161_ANCHORS.md) for the issuance protocol, offline import, timestamp-unit requirements, trust assumptions, and remaining limitations.

## Generated outputs

The build emits:

```text
bundle.canonical.json           canonical proof-carrying handoff
bundle.pretty.json              human-readable rendering of the same object
execution-result.canonical.json canonicalized empirical stdout
GeneratedCertificate.lean      generated Lean witness
```

The checked-in fixture is reproducibility-tested with:

```bash
python -m tools.lfv_adapter check-generated \
  --spec examples/reference_adapter/experiment.json \
  --bundle examples/reference_adapter/generated/bundle.canonical.json \
  --lean LeanFinance/Generated/ReferenceAdapter.lean \
  --allow-local-anchor
```

## Lineage time ordering

A feature must not merely have all inputs available by the final decision. Each input must be available by the feature's own `generatedAt` timestamp. The Lean `ArtifactAvailableAt.feature` constructor carries recursive input proofs at that earlier timestamp, and the adapter enforces the same relation before generating a witness.

This rejects the following invalid history even when every item exists by decision time 10:

```text
dataset available at 8
feature generated at 6
final decision at 10
```

## Trust boundary

| Layer | Checked property |
|---|---|
| Python adapter | canonical encoding, digest shape, recomputed ledger commitments, registration order, anchor/ledger equality, selected trial match, command exit status, JSON result shape, point-in-time lineage |
| RFC 3161 verifier | original request/response pairing, nonce and imprint equality, signed-token status, TSA certificate chain and timestamp-signing purpose, generation time, evidence/trust-bundle hashes |
| Generated Lean witness | manifest/result/parameter binding, no-future-information propositions, recursively closed lineage, ledger structure, anchor relation, selected preregistered trial |
| Remaining external evidence | correctness of raw data and empirical code, independent TSA behavior, distribution of the correct trust root, host/OpenSSL integrity, certificate revocation and long-term archival evidence |

The execution command is trusted input. It is invoked as an argument vector with `shell=False`, a bounded timeout, closed stdin, captured stdout/stderr, and `PYTHONHASHSEED=0`.

## Schemas

- `schemas/lfv-experiment-spec-v1.schema.json`
- `schemas/lfv-proof-carrying-backtest-bundle-v1.schema.json`
- `schemas/lfv-ledger-anchor-v1.schema.json`

The adapter's built-in validator is normative for this reference implementation; the JSON Schema files are interoperability aids.
