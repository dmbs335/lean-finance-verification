# Lean Finance Verification

A Lean 4 research framework for **proof-carrying financial research**: market models,
constraint-driven dynamics, hidden-state inference, operator representations, industrial
bottlenecks, and machine-checkable backtest certificates.

## What this repository verifies

The project deliberately separates empirical estimation from formal claims. Python,
Rust, or another external system may estimate parameters and produce artifacts; Lean
checks the logical contract attached to those artifacts.

Current certificate properties include:

- every dataset or market observation used by a decision was available at the decision time;
- every derived feature was generated no later than the decision time;
- the selected parameter set appears in the declared search ledger;
- code, data, parameters, environment, model family, and result are hash-bound;
- finite latent-state posteriors are normalized and carry bounded weights;
- metastability claims carry an internal-mixing/exit-time separation and retention floor;
- committor-style transition claims lie inside their declared boundary interval;
- cumulative first-passage probabilities are monotone across horizons;
- local non-expansiveness composes over every certified finite horizon;
- control plans witness exact reachability, and observation traces witness pairwise observability;
- a proposed finite Koopman lift intertwines state and feature evolution at every finite horizon;
- a bifurcation claim crosses a declared critical parameter under one model family and changes
  its certified stability class.

These properties do **not** prove that a strategy is profitable, that a statistical model is
correct, that a market truly has a low-dimensional attractor, or that estimated chaos is
deterministic. They prove the narrower assumptions and claim boundaries encoded by each
certificate.

## Formal layers

```text
LeanFinance/
├── GameTheory/       heterogeneous players, beliefs, feasibility, best responses
├── Market/           order flow, linear price impact, Kyle-style quoting, liquidity
├── Constraints/      margin, VaR, redemption, and short-cover triggers
├── Dynamics/         market-state and equilibrium-regime transitions
├── Inference/        latent state, identification, and inverse-game definitions
├── StateSpace/       posterior, metastability, stability, control, Koopman, bifurcation
├── StrategyEcology/  causal strategy-interaction kernels and identification
├── SupplyChain/      dynamic capacity bottlenecks and rent-capture certificates
├── Backtest/         point-in-time data, lineage, search ledger, reproducibility
└── Certificate/      data, strategy, backtest, and verified-claim certificates
```

## State-space verification boundary

The `StateSpace` layer treats empirical outputs as untrusted inputs and checks contracts
around them:

1. `StateEstimateCertificate` checks point-in-time observations, hashes, and posterior mass.
2. `MetastabilityCertificate` checks declared time-scale separation and retention.
3. `TransitionBoundaryCertificate` checks a committor score against a declared transition band.
4. `LocalStabilityCertificate` proves that a supplied non-expansive relation remains
   non-expansive over finite iteration inside a forward-invariant domain.
5. `ControlPlanCertificate` and `PairObservabilityCertificate` provide constructive finite
   reachability and distinguishability witnesses.
6. `KoopmanCertificate` extends one-step intertwining to every finite horizon.
7. `BifurcationClaimCertificate` prevents a generic regime change from being mislabeled as a
   bifurcation without a critical crossing, a stability-class change, and one model family.

The empirical pipeline must still justify state identification, calibration, Jacobian or
operator estimation, sampling uncertainty, and out-of-sample validity.

## Build

Lean is pinned in `lean-toolchain`.

```bash
lake build
```

GitHub Actions runs the same build on `main`, feature branches, and pull requests.

## Research roadmap

1. Replace integer-valued toy primitives with reusable ordered-ring and probability abstractions.
2. Connect state-space certificates to serialized posterior particles and point-in-time data.
3. Formalize finite Markov kernels, almost-invariant sets, and executable committor solvers.
4. Add matrix/Jacobian certificates for spectral and non-normal finite-time stability bounds.
5. Add controlled Koopman operators and robust stochastic reachability.
6. Build a reference proof-carrying state-based allocation pipeline end to end.

## Scope

This repository is research software. A Lean proof is only as strong as its formalized
assumptions and the cryptographic/data-lineage evidence supplied to the checker.
