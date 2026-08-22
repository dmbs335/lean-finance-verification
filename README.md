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
- the complete ledger prefix is bound to a pre-decision external anchor contract;
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

GitHub Actions runs Python adapter tests, checks that generated artifacts are
byte-reproducible, and then runs the Lean build.

## Python reference adapter

The repository contains a dependency-free reference adapter that executes a declared
empirical command, canonicalizes its JSON result, hashes all research artifacts,
checks the committed search ledger and anchor, and emits both a canonical bundle and a
Lean `CertifiedAdapterOutput` witness.

```bash
python -m tools.lfv_adapter build \
  --spec examples/reference_adapter/experiment.json \
  --out /tmp/lfv-reference \
  --allow-local-anchor
```

The local anchor flag is only for the checked-in fixture; it is not a substitute for an
independently published timestamp. See [`docs/REFERENCE_ADAPTER.md`](docs/REFERENCE_ADAPTER.md)
for the serialization contract, preregistration flow, trust boundary, and schemas.

## Research roadmap

1. Replace integer-valued toy market primitives with reusable ordered-ring and
   probabilistic abstractions.
2. Formalize a finite Bayesian market game and executable equilibrium checker.
3. Connect forced-flow composition, constraint activation, and regime-transition
   safety theorems end to end.
4. Add authenticated adapters for external transparency logs or timestamp services.
5. Run the reference adapter against a real point-in-time dataset and preserve the
   resulting certificate bundle as a reproducible research artifact.

## Scope

This repository is research software. A Lean proof is only as strong as its formalized
assumptions and the cryptographic, data-lineage, execution, and external-anchor evidence
supplied to the checker.
