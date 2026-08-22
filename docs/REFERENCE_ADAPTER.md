# Python Reference Adapter

`tools/lfv_adapter` is the executable boundary between an empirical backtest and the Lean contracts in `LeanFinance/Backtest`.

It performs five operations in one deterministic pipeline:

1. hashes source files, datasets, parameters, and the declared environment;
2. verifies a commitment-chained search ledger and its pre-decision anchor;
3. executes the empirical command without a shell and requires canonicalizable JSON output;
4. checks point-in-time data and transitive feature-lineage ordering;
5. emits a canonical certificate bundle and a concrete Lean `CertifiedAdapterOutput` witness.

The adapter does not prove profitability, data truth, model correctness, or the authenticity of an external timestamp provider. Those remain outside the Lean kernel.

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

## Reference flow

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

`make-local-anchor` is only a fixture utility. It proves that the anchor structurally binds the terminal ledger commitment and entry count, but it is not external timestamp evidence. Production runs should replace it with evidence published by an independent append-only or timestamping service and omit `--allow-local-anchor`.

The build emits:

```text
bundle.canonical.json          canonical proof-carrying handoff
bundle.pretty.json             human-readable rendering of the same object
execution-result.canonical.json canonicalized empirical stdout
GeneratedCertificate.lean     generated Lean witness
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

A feature must not merely have all inputs available by the final decision. Each input must be available by the feature's own `generatedAt` timestamp. The Lean `ArtifactAvailableAt.feature` constructor now carries recursive input proofs at that earlier timestamp, and the adapter enforces the same relation before generating a witness.

This rejects the following invalid history even when every item exists by decision time 10:

```text
dataset available at 8
feature generated at 6
final decision at 10
```

## Trust boundary

| Layer | Checked property |
|---|---|
| Python adapter | canonical encoding, digest shape, recomputed ledger commitments, timestamp order, anchor/ledger equality, selected trial match, command exit status, JSON result shape, point-in-time lineage |
| Generated Lean witness | manifest/result/parameter binding, no-future-information propositions, recursively closed lineage, ledger structure, anchor relation, selected preregistered trial |
| External evidence | correctness of raw data, correctness of the empirical program, cryptographic implementation/runtime integrity, authenticity and non-equivocation of the anchor provider |

The execution command is trusted input. It is invoked as an argument vector with `shell=False`, a bounded timeout, closed stdin, captured stdout/stderr, and `PYTHONHASHSEED=0`.

## Schemas

- `schemas/lfv-experiment-spec-v1.schema.json`
- `schemas/lfv-proof-carrying-backtest-bundle-v1.schema.json`

The adapter's built-in validator is normative for this reference implementation; the JSON Schema files are interoperability aids.
