# Causal Financial Computation Layer

This layer separates a financial engine's calculation ability from the evidence needed to trust one application of that calculation.

```text
financial engine
  computes prices, risks, signals, orders, and PnL

LFV causal control plane
  checks which inputs were available, which registered implementation ran,
  whether future extensions can change the past, and which artifacts were bound
```

## Combined contract

A computation is admitted only when the relevant contracts hold:

```text
Temporal contract
  causally equivalent prefixes produce equal past outputs
  selected observations were actually available
  evaluation does not mutate the supplied source

Formula contract
  formula and implementation identities match a preregistered definition
  inputs are timely, unit-compatible, valuation-aligned, and model-aligned
  domain conditions hold
  an exact output is bound to the exact input and output artifacts

Composition contract
  local data, formula, decision, execution, and result certificates
  refer to the same causal pipeline
```

This does not replace a pricing, risk, or backtest engine. It makes the engine's hidden assumptions and causal boundaries machine-checkable.

## Current controlled results

The temporal semantic fuzzer admits only causal forward fill among its controlled engines. Unsafe engines expose future-extension, late-release, bidirectional-interpolation, representation, and source-mutation failures with exact first-divergence witnesses.

The formula corpus certifies only one of nine hedge-scale applications. Several rejected applications use the correct formula and return the correct number, but violate temporal, unit, model-version, preregistration, or output-boundary obligations.

## Research progression

This causal layer is the foundation for:

1. a concrete gs-quant adapter that captures actual engine traces;
2. dimension and scale algebra for decimal, percent, basis-point, annualized, and period returns;
3. risk-model and security-master revision attribution;
4. execution-realizability intervals and certifiable capacity;
5. PnL explain closure with bounded residuals;
6. minimum adversarial scenario-basis synthesis.

## Boundary

The current benchmarks are finite and exact. They do not establish external publication-time truth, risk-model accuracy, floating-point or concurrency coverage, or future strategy profitability.
