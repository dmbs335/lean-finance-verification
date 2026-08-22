# Lean Finance Verification

A Lean 4 research framework for **proof-carrying financial research**: market models,
constraint-driven dynamics, inverse-game abstractions, industrial bottlenecks, and
machine-checkable backtest certificates.

## What this repository verifies

The project deliberately separates empirical estimation from formal claims. Python,
Rust, or another external system may estimate parameters and produce artifacts; Lean
checks the logical contract attached to those artifacts.

Current certificate properties include:

- every dataset used by a decision was available at the decision time;
- every derived feature has recursively closed lineage, with each input available by
  the feature's own generation time;
- the selected code/parameter trial appears in a commitment-chained search ledger;
- the complete ledger prefix is bound to a pre-decision anchor;
- RFC 3161 anchors are re-verified against verifier-selected TSA trust, including the
  original nonce, message imprint, signed response, certificate chain, and generation
  time;
- code, data, parameters, environment, features, and result are domain-separated by
  artifact kind, canonical schema, hash algorithm, and digest;
- an adapter handoff exposes a proof-carrying certificate rather than an opaque
  performance number.

These properties do **not** prove that a strategy is profitable, that raw data is true,
or that an empirical model is statistically correct. They prove the narrower
research-integrity claims encoded by the certificate.

## Formal layers

```text
LeanFinance/
├── GameTheory/       heterogeneous players, beliefs, feasibility, best responses
├── Market/           order flow, linear price impact, Kyle-style quoting, liquidity
├── Constraints/      margin, VaR, redemption, and short-cover triggers
├── Dynamics/         market-state and equilibrium-regime transitions
├── Inference/        latent state, identification, and inverse-game boundaries
├── StrategyEcology/  context-dependent causal strategy interactions
├── SupplyChain/      dynamic capacity, substitution, qualification, and rent claims
├── Backtest/         artifacts, PIT lineage, anchored search history, adapter contract
├── Certificate/      data, strategy, backtest, and verified-claim certificates
└── Generated/        adapter-emitted concrete Lean witnesses
```

## Build

Lean is pinned in `lean-toolchain`.

```bash
lake build
```

GitHub Actions runs Python adapter tests, including a locally generated RFC 3161 test
PKI and signed timestamp, checks that generated artifacts are byte-reproducible, and
then runs the Lean build.

## Python reference adapter

The repository contains a dependency-free reference adapter that executes a declared
empirical command, canonicalizes its JSON result, hashes all research artifacts,
checks the committed search ledger and anchor, and emits both a canonical bundle and a
Lean `CertifiedAdapterOutput` witness.

The checked-in deterministic fixture uses a deliberately non-authoritative local
anchor:

```bash
python -m tools.lfv_adapter build \
  --spec examples/reference_adapter/experiment.json \
  --out /tmp/lfv-reference \
  --allow-local-anchor
```

A production ledger can instead be anchored by an RFC 3161 TSA:

```bash
python -m tools.lfv_adapter make-rfc3161-anchor \
  --ledger research/search-ledger.json \
  --tsa-url https://tsa.example.org/ \
  --rfc3161-ca-file trust/tsa-roots.pem \
  --out research/ledger-anchor.json
```

The TSA signing trust bundle is selected externally by the verifier and is hashed into
the evidence binding. See [`docs/REFERENCE_ADAPTER.md`](docs/REFERENCE_ADAPTER.md) for
the complete adapter flow and [`docs/RFC3161_ANCHORS.md`](docs/RFC3161_ANCHORS.md) for
signed timestamp issuance, verification, and trust assumptions.

## Research roadmap

1. Replace integer-valued toy market primitives with reusable ordered-ring and
   probabilistic abstractions.
2. Formalize a finite Bayesian market game and executable equilibrium checker.
3. Connect forced-flow composition, constraint activation, and regime-transition
   safety theorems end to end.
4. Add a second independent transparency-log anchor and require multi-provider quorum
   for high-assurance preregistration.
5. Run the reference adapter against a real point-in-time dataset and preserve the
   resulting certificate bundle as a reproducible research artifact.

## Scope

This repository is research software. A Lean proof is only as strong as its formalized
assumptions and the cryptographic, data-lineage, execution, external-anchor, and trust-
material evidence supplied to the checker. RFC 3161 support verifies signed evidence
but does not by itself prove TSA independence, revocation status, or long-term archival
validity.
