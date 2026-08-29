# Proof-Carrying PnL Explain Closure

A table of risk attributions is not automatically a complete explanation of realized PnL. The arithmetic, time boundary, model identity, portfolio identity, market snapshots, non-market components, and residual tolerance must all be checked independently.

## Upstream formula mapping

The public GS Quant 2.1.6 implementation of `BackTest.pnl_explain` computes each registered attribute from the previous-date risk and a market-data move. In simplified notation:

```text
first order  = scaling × previous risk × Δmarket
second order = 1/2 × scaling × previous risk × (Δmarket)^2
```

The public method returns cumulative per-attribute series. Its docstring describes the result as risk attributions explaining PnL, but the public method does not itself emit a total realized-PnL closure certificate, an explicit residual bound, or cross-object digest bindings.

The five closure-state fixtures remain `STATIC_REVIEW_THEORY_MAPPED` and do not
import GS Quant. A separate pinned conformance fixture executes the public GS
Quant 2.1.6 method on controlled local inputs and binds the method source,
fixture, runtime output, and LFV recomputation in a replayable report.
The v2 fixture contains three positions and permits separate `results` and
`exit_results` snapshots on one date. It therefore directly exercises partial
portfolio exits instead of treating every date as an all-retained or all-exited
single-position state.

Pinned upstream reference:

```text
repository: goldmansachs/gs-quant
branch:     master
commit:     fa9dd42f0677a0d2fb5819fca6e2f67de9458c06
release:    2.1.6
module:     gs_quant.backtests.backtest_objects
symbol:     BackTest.pnl_explain
```

## Local quadratic theory

For one factor, register a local quadratic approximation around the previous valuation point:

```text
V_after(move)
= V_before
+ firstSensitivity × move
+ halfSecondSensitivity × move²
```

`halfSecondSensitivity` already contains the Taylor factor one-half. The Lean theorem proves exact arithmetic closure of this declared model:

```text
V_after(move) - V_before
= first-order PnL + second-order PnL
```

This theorem does **not** prove that a real pricing function is globally quadratic or that supplied sensitivities are correct. It proves the arithmetic consequence of the registered local approximation.

For a smooth real price function, the theoretical motivation is the multivariate Taylor expansion:

\[
\Delta V
= \nabla V(x_0)^T\Delta x
+ \frac12\Delta x^T H_V(x_0)\Delta x
+ R_3.
\]

A production residual certificate would additionally require a bound on the third and higher derivatives. The present controlled integer model treats the unmodeled remainder empirically as the closure residual.

## Global reconstruction

The complete controlled reconstruction is:

\[
PnL_{reconstructed}
= \sum_i Attribution_i
+ Carry
+ Trades
+ Cashflows
- TransactionCost
+ ModelRevision.
\]

Residual is:

\[
Residual
= PnL_{realized} - PnL_{reconstructed}.
\]

A preregistered tolerance \(\varepsilon\) produces three states.

```text
CLOSED
  local formulas, temporal availability, and bindings are valid
  |Residual| ≤ ε

PARTIAL
  local formulas, temporal availability, and bindings are valid
  |Residual| > ε

OPEN
  at least one formula, time, portfolio, market-data, model, or result binding fails
```

A small residual cannot repair a binding failure. Conversely, a material residual does not invalidate locally correct attributions; it means the selected basis is incomplete or an unmodeled component remains.

## Cross-object binding

Every factor attribution and the realized result must share:

```text
portfolio hash
market-data-before hash
market-data-after hash
model id and version
valuation-before timestamp
valuation-after timestamp
```

The controlled counterexample deliberately substitutes the portfolio hash on one locally correct factor. The first- and second-order arithmetic still passes, but the explanation remains `OPEN` because local formula validity does not imply global causal identity.

This is an application of the repository's Certificate Composition Law:

```text
local attribution correctness
+ same-pipeline binding
+ residual bound
→ CLOSED PnL explanation
```

## Controlled results

The fixture contains five cases.

```text
closed-small-residual
  market explain   44
  non-market       16
  reconstructed    60
  realized         61
  residual          1
  tolerance         2
  status        CLOSED

partial-material-residual
  reconstructed    60
  realized         70
  residual         10
  tolerance         2
  status       PARTIAL

open-substituted-portfolio
  local formulas valid
  one factor refers to another portfolio
  status          OPEN

open-formula-mismatch
  claimed first-order term differs from exact registered expression
  status          OPEN

open-future-attribution
  attribution became available after the decision boundary
  status          OPEN
```

## Commands

```bash
python -m tools.pnl_explain_closure analyze \
  --model examples/pnl_explain_closure/controlled.json \
  --out /tmp/pnl-explain-closure.json

python -m tools.pnl_explain_closure verify \
  --model examples/pnl_explain_closure/controlled.json \
  --report /tmp/pnl-explain-closure.json

python -m pip install gs-quant==2.1.6
python -m tools.pnl_explain_closure gs-quant-conformance \
  --model examples/pnl_explain_closure/gs_quant_conformance.json \
  --out /tmp/gs-quant-pnl-conformance.json
python -m tools.pnl_explain_closure verify-gs-quant-conformance \
  --model examples/pnl_explain_closure/gs_quant_conformance.json \
  --report examples/pnl_explain_closure/generated/gs-quant-conformance.canonical.json
```

## Assurance boundary

### Lean-proved

- exact closure of the declared local quadratic integer model;
- consequences carried by a CLOSED certificate;
- controlled examples separating local formula validity from global binding.

### Exact Python computation

- first- and second-order arithmetic;
- non-market reconstruction;
- residual and tolerance status;
- temporal and identity gates;
- deterministic report recomputation and tamper rejection;
- pinned GS Quant version and normalized method-source binding;
- direct first-order, second-order, multi-position aggregation, same-date
  retained/exit, zero-risk skip, portfolio transition, and fractional-output
  runtime comparison against independent exact-rational LFV recomputation;
- fail-closed portfolio-topology validation: no overlapping current/exit
  position, orphan exit, or silently dropped previous position.

### Not established

- correctness or calibration of real sensitivities;
- a bound on higher-order Taylor remainder;
- behavior on production portfolio and risk-result object implementations;
- completeness of the attribution basis;
- truth of external portfolio, model, or market-data metadata;
- Goldman Sachs internal or remote server-side semantics not present in the
  public repository.

## Next extension

The next mathematical layer is a bounded third-order remainder and an attribution-basis CEGIS loop: find a market path with residual above tolerance, identify a missing cross-greek or non-market component, extend the basis, and reissue the closure certificate.
