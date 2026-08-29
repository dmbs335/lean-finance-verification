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
  DIRECT_TESTED on controlled local inputs
  ADAPTER_BOUND to version, method source, model, and output digests
  controlled closure cases: yes
  direct runtime: GS Quant 2.1.6 executed
  adapter binding: deterministic replay implemented
  portfolio topology: multi-instrument aggregation and same-day partial exits
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
| Direct upstream runtime | 0 | GS Quant 2.1.6 controlled execution | +1 pinned runtime |
| Direct upstream APIs executed | 0 | 1 | + `BackTest.pnl_explain` |
| Upstream symbols statically mapped | GenericDataSource family | + `BackTest.pnl_explain` | +1 symbol |
| Controlled closure cases | 0 | 5 | +5 |
| Direct runtime topology | single instrument | 3 instruments, retained + exited on the same date | mixed path added |
| PnL regression tests | 21 | 26 | +5 |
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
- rejection of overlapping current/exit positions, unaccounted previous
  positions, duplicate date/location snapshots, and weakened path coverage.

### Not established

- conformance of remote Marquee services or Goldman Sachs internal packages;
- correctness or calibration of real risk sensitivities;
- completeness of the attribution basis;
- higher-order Taylor remainder bounds;
- cross-greek treatment;
- unit correspondence with live GS Quant risk objects;
- Goldman Sachs internal or server-side semantics.

## Direct-coverage implementation

`tools.pnl_explain_closure gs-quant-conformance` executes the pinned public
`BackTest.pnl_explain` method against a local controlled object. The adapter
binds GS Quant version 2.1.6 and the normalized method-source digest. The v2
fixture executes first-order, second-order, multi-instrument aggregation,
same-date retained/exit positions, full exit, portfolio transition, zero-risk
skip, and fractional cumulative-output paths,
canonicalizes cumulative outputs as exact rational strings, and compares them
with an independent LFV `Fraction` recomputation. Version drift, source
substitution, missing metrics, arithmetic divergence, and report tampering fail
closed. CI also compares the replay byte-for-byte with
`examples/pnl_explain_closure/generated/gs-quant-conformance.canonical.json`.
