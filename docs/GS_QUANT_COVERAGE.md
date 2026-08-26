# GS Quant Coverage Ledger

This ledger tracks integration with the public `goldmansachs/gs-quant` repository. It is not source-line coverage. Controlled fixtures, static review, direct upstream execution, adapter binding, and Lean connection are reported separately.

## Upstream baseline

```text
repository: goldmansachs/gs-quant
branch:     master
commit:     fa9dd42f0677a0d2fb5819fca6e2f67de9458c06
release:    2.1.6
checked:    2026-08-26
```

Public/internal boundaries matter: absence from the public repository does not establish absence from Goldman Sachs internal packages or Marquee services.

## Status vocabulary

```text
NOT_STARTED
STATIC_REVIEW
THEORY_MAPPED
CONTROLLED
DIRECT_TESTED
ADAPTER_BOUND
FORMALLY_CONNECTED
EMPIRICALLY_EVALUATED
```

## Current cumulative map

### Data-source semantics

```text
gs_quant.backtests.data_sources.GenericDataSource.get_data
  STATIC_REVIEW
  CONTROLLED temporal analog
  direct runtime: not executed

MissingDataStrategy.fill_forward / interpolate
  STATIC_REVIEW
  CONTROLLED temporal analog
  direct runtime: not executed
```

Covered controlled properties:

- future-extension invariance;
- post-cutoff revision sensitivity;
- causal availability;
- source immutability;
- timestamp representation equivalence;
- first-divergence witnesses.

### Formula application

```text
public quantitative formulas
  THEORY_MAPPED through LFV formula contracts

specific GS Quant runtime objects
  NOT_STARTED
```

The LFV contract checks formula/implementation identity, units, valuation time, model version, domain conditions, temporal availability, and input/output artifact binding.

### PnL explain — current iteration

```text
gs_quant.backtests.backtest_objects.BackTest.pnl_explain
  STATIC_REVIEW
  THEORY_MAPPED
  controlled closure cases: yes
  direct runtime: not executed
  adapter binding: not started
```

Mapped public arithmetic:

```text
first order  = scaling × previous risk × market move
second order = 1/2 × scaling × previous risk × market move²
```

LFV adds obligations not emitted by the controlled upstream mapping:

- exact local formula recomputation;
- attribution availability by the decision boundary;
- common portfolio, market-snapshot, model-version, and valuation binding;
- non-market PnL reconstruction;
- realized-result binding;
- preregistered residual tolerance;
- `CLOSED`, `PARTIAL`, and `OPEN` classification.

## PnL iteration delta

| Coverage area | Previous | Current | Delta |
|---|---|---|---|
| Direct upstream runtime | 0 | 0 | 0 |
| Direct upstream APIs executed | 0 | 0 | 0 |
| Upstream symbols statically mapped | GenericDataSource family | + `BackTest.pnl_explain` | +1 symbol |
| Controlled PnL cases | 0 | 5 | +5 |
| PnL regression tests | 0 | 9 | +9 |
| PnL closure states | none | CLOSED / PARTIAL / OPEN | +3 states |
| Lean PnL modules | 0 | 2 source modules + umbrella | new |
| Global binding counterexamples | 0 | portfolio substitution | +1 class |

## Assurance boundary

### Lean-proved

- exact arithmetic closure of the declared local quadratic integer model;
- consequences carried by a CLOSED PnL explanation certificate;
- controlled separation of local formula validity from global pipeline binding.

### Exact finite Python checks

- first- and second-order term recomputation;
- non-market PnL reconstruction;
- residual and tolerance classification;
- temporal and cross-object binding gates;
- deterministic replay and tamper rejection.

### Not established

- conformance of the live GS Quant runtime;
- correctness or calibration of real risk sensitivities;
- completeness of the attribution basis;
- higher-order Taylor remainder bounds;
- cross-greek treatment;
- unit correspondence with live GS Quant risk objects;
- Goldman Sachs internal or server-side semantics.

## Next direct-coverage milestone

Build a read-only adapter that executes the pinned public `BackTest.pnl_explain` path on a local controlled `BackTest` object, captures risk and market-data inputs, canonicalizes the returned attribution series, and compares it with the LFV recomputation. Only after this step may `BackTest.pnl_explain` advance from `THEORY_MAPPED` to `DIRECT_TESTED` or `ADAPTER_BOUND`.
