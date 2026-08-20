# Lean Finance Verification

A Lean 4 research framework for **proof-carrying financial research**: market models,
constraint-driven dynamics, inverse-game abstractions, and machine-checkable backtest
certificates.

## What this repository verifies

The project deliberately separates empirical estimation from formal claims. Python,
Rust, or another external system may estimate parameters and produce artifacts; Lean
checks the logical contract attached to those artifacts.

Current certificate properties include:

- every dataset used by a decision was available at the decision time;
- every derived feature was generated no later than the decision time;
- the selected parameter set appears in the declared search ledger;
- code, data, parameters, environment, and result are bound by non-empty hashes;
- a verified claim carries the proofs required by the certificate type.

These properties do **not** prove that a strategy is profitable or that an empirical
model is statistically correct. They prove the narrower research-integrity claims
encoded by the certificate.

## Formal layers

```text
LeanFinance/
├── GameTheory/     heterogeneous players, beliefs, feasibility, best responses
├── Market/         order flow, linear price impact, Kyle-style quoting, liquidity
├── Constraints/    margin, VaR, redemption, and short-cover triggers
├── Dynamics/       market-state and equilibrium-regime transitions
├── Inference/      latent state and inverse-game problem definitions
├── Backtest/       point-in-time data, lineage, search ledger, reproducibility
└── Certificate/    data, strategy, backtest, and verified-claim certificates
```

## Build

Lean is pinned in `lean-toolchain`.

```bash
lake build
```

GitHub Actions runs the same build on `main`, feature branches, and pull requests.

## Research roadmap

1. Replace integer-valued toy primitives with reusable ordered-ring abstractions.
2. Formalize a finite Bayesian market game and executable equilibrium checker.
3. Add forced-flow composition and equilibrium-transition safety theorems.
4. Define a serialization format for certificates emitted by empirical pipelines.
5. Build a reference proof-carrying backtest end to end.

## Scope

This repository is research software. A Lean proof is only as strong as its formalized
assumptions and the cryptographic/data-lineage evidence supplied to the checker.
