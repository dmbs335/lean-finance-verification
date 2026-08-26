# Causal Financial Computation Layer

This milestone adds an epistemic control plane above financial calculation engines.

```text
financial engine
  computes prices, risks, signals, orders, and PnL

LFV causal layer
  proves which inputs were available, which formula was applied,
  which artifacts were bound, and whether future extensions can change the past
```

## Combined contract

A result is admitted only when both sides hold:

```text
Temporal contract
  unavailable future inputs cannot affect a past output
  the data source is not mutated by observation

Formula contract
  registered definition and implementation match
  inputs are timely, unit-compatible, valuation-aligned, model-aligned
  domain conditions hold
  the exact output is bound to the exact input artifacts
```

This does not replace a pricing or risk engine. It makes the engine's hidden assumptions and causal boundaries machine-checkable.

## Research progression

The new layer is the foundation for:

1. backend adapters that capture actual gs-quant traces under future-extension and representation transformations;
2. unit/scale algebra for decimal, percent, basis-point, annualized, and period returns;
3. risk-model and security-master revision attribution;
4. execution-realizability intervals and certifiable capacity;
5. PnL explain closure with bounded residuals;
6. minimum adversarial scenario-basis synthesis.

The first controlled benchmark is intentionally finite and exact. It turns silent numerical corruption into a minimized counterexample rather than a plausible but unaudited return number.
