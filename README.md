# Lean Finance Verification

A Lean 4 research framework for machine-checkable claims about financial
market models and quantitative research pipelines.

## What this project verifies

The project deliberately does **not** prove that a strategy is profitable or
will continue to work. It verifies narrower, auditable claims such as:

- every dataset used by a decision was available at that decision time;
- datasets, code, parameters, and environments are content-addressed;
- feature lineage was generated before the decision;
- the tested parameterization appears in the disclosed search ledger;
- a backtest result is bound to those proofs as a proof-carrying certificate.

The formal core also contains small, composable definitions for heterogeneous
players, beliefs, best responses, Bayesian games, order flow, Kyle-style price
impact, funding constraints, equilibrium transitions, and hidden-state
observation models.

## Build

The repository pins Lean `v4.30.0`.

```bash
lake build
lake exe leanFinance
```

GitHub Actions runs the same build on every push and pull request.

## Architecture

```text
LeanFinance/
├── GameTheory/      # players, beliefs, payoff, best response, equilibrium
├── Market/          # orders, order flow, liquidity, Kyle price formation
├── Constraints/     # margin and VaR activation
├── Dynamics/        # market and equilibrium transitions
├── Inference/       # latent state / observation compatibility
├── Backtest/        # point-in-time data, lineage, search ledger, result
└── Certificate/     # proof-carrying strategy, data, and backtest objects
```

## Core soundness statement

`LeanFinance.Certificate.certificate_sound` proves that every constructed
`BacktestCertificate` entails:

1. no future information was used;
2. the experiment is reproducibly identified;
3. the selected parameterization is recorded;
4. all feature lineages are valid at the decision time.

A certificate can only be constructed by supplying proofs for these
obligations.

## Research roadmap

1. Add non-vacuous toy equilibria and a finite-game solver interface.
2. Formalize constraint activation and forced-liquidation propagation.
3. Define certificate serialization and an external verifier protocol.
4. Connect Python estimators to a small proof-producing certificate compiler.
5. Add point-in-time corporate-action, universe, and cost-model guarantees.
6. Model equilibrium transitions and partially identified inverse games.

## Design rule

> Empirical systems estimate; Lean checks the exact claim and its assumptions.
