# Finite Robust-POMDP Bellman Foundation

The one-step belief layer identifies which hidden regimes remain possible after an observation. This module adds finite-horizon backward induction over a discretized belief graph and a family of transition/observation models.

For one action and model:

```text
Q(model, belief, action)
= net immediate reward
+ discount × weighted mean(previous-horizon successor value)
```

The robust action value is the minimum over admitted models; the state value is the maximum robust action value. Python performs every backup with exact rational arithmetic. Lean checks cross-multiplied lower-bound certificates for each model and proves those bounds survive model-family refinement.

## Controlled two-step result

At horizon one:

```text
stable → increase, robust value 5
stress → reduce, robust value 3
```

At the uncertain initial belief, acting immediately yields at most 1 bp robust value from `hold`. The `query` action pays 1 bp and branches to `stable` or `stress`.

```text
optimistic model query value = 7/2
adverse model query value    = 5/2
robust query value           = 5/2
```

Therefore the horizon-two robust policy selects `query`, not an immediate trade.

## Assurance boundary

This is a finite discretized belief graph. Branch weights are declared model inputs, not calibrated probabilities. The module does not prove observation-model correctness, continuous-belief approximation error, asymptotic convergence, market causality, or profitability. It provides the exact multi-step control certificate needed before a bounded tree-search layer is introduced.
