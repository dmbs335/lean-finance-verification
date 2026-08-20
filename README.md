# Lean Finance Verification

A Lean 4 research framework for machine-checkable claims about financial
market models, inverse games, and quantitative research pipelines.

## What this project verifies

The project deliberately does **not** prove that a strategy is profitable or
will continue to work. It verifies narrower, auditable claims such as:

- every dataset used by a decision was available at that decision time;
- datasets, code, parameters, environments, and cost models are identified;
- feature lineage was generated before the decision and is bound to certified
  dataset hashes;
- the tested parameterization appears in the disclosed search ledger;
- the strategy and parameterization match a pre-evaluation commitment;
- every security in a certified universe was active at the decision time;
- future-only research artifacts cannot alter a point-in-time decision;
- a backtest result is bound to those proofs as a proof-carrying certificate.

The formal core also contains composable definitions for heterogeneous
players, beliefs, best responses, Bayesian games, order flow, Kyle-style price
impact, funding constraints, equilibrium transitions, and hidden-state
observation models.

## Build

The repository pins Lean `v4.30.0`.

```bash
lake build
lake exe leanFinance
```

GitHub Actions is configured to run the build on pushes and pull requests.

## Architecture

```text
LeanFinance/
├── GameTheory/       # players, beliefs, payoff, best response, equilibrium
├── Market/           # orders, order flow, liquidity, Kyle price formation
├── Constraints/      # margin and VaR activation
├── Dynamics/         # market and equilibrium transitions
├── Inference/        # latent states, observational equivalence, identification
├── Backtest/         # point-in-time data, universe, lineage, costs, result
├── ResearchIntegrity/# commitments and future-artifact noninterference
└── Certificate/      # proof-carrying strategy, data, universe, backtest objects
```

## Core soundness statement

`LeanFinance.Certificate.certificate_sound` proves that every constructed
`BacktestCertificate` entails all of the following:

1. no future information was used;
2. all datasets are well-formed and content-addressed;
3. the point-in-time universe is valid and aligned with the decision;
4. the transaction-cost model was locked before the decision;
5. code and parameters match a valid prior commitment;
6. the experiment is reproducibly identified;
7. the selected parameterization is recorded in the search ledger;
8. feature lineages are timely and bound to certified inputs;
9. the empirical claim is nonempty and generated after the decision.

A certificate can only be constructed by supplying proofs for these
obligations.

## Inverse-game identification

The inverse-game layer distinguishes full primitive recovery from recovery of
an identifiable target. `Identified observe target` means the target is
constant on every observational-equivalence class.

The formal core proves:

- a target that factors through public observations is identified;
- post-processing preserves identification;
- one equal-observation/different-target pair proves non-identifiability;
- aggregate flow alone need not identify hidden payoff type;
- an enriched observation can identify constraint activation.

See `docs/INVERSE_GAME_IDENTIFICATION.md`.

## Research roadmap

1. Add a finite-game solver interface with certificates for computed best
   responses and equilibria.
2. Formalize forced-liquidation propagation and equilibrium instability.
3. Define certificate serialization and an external verifier protocol.
4. Connect Python estimators to a proof-producing certificate compiler.
5. Add corporate-action, benchmark, hypothesis-completeness, and signed archive
   guarantees.
6. Build identified-set inference for partially observed strategic markets.

## Design rule

> Empirical systems estimate; Lean checks the exact claim and its assumptions.
