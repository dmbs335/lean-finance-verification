# Belief-State Robust Control Foundation

The earlier finite control layer assumes the state is observed. This module introduces a one-step partially observed foundation: hidden regimes carry prior weights, observations carry likelihood weights, and the posterior is computed exactly as:

```text
posteriorWeight(hidden) = priorWeight(hidden) × likelihood(observation, hidden)
```

Normalization does not change support. Lean proves zero-likelihood and zero-prior hypotheses receive zero posterior weight, and that support refinement cannot decrease the greatest robust lower bound for a fixed action.

## Controlled hidden-regime example

The prior support contains `bull`, `base`, and `bear`. The immediate worst-case action is `hold` at 1 bp.

A `stable` observation produces unnormalized posterior weights:

```text
bull 8, base 10, bear 0
```

The bear regime is removed and `increase` has robust net value 5.

A `stress` observation produces:

```text
bull 0, base 5, bear 12
```

The bull regime is removed and `reduce` has robust net value 3.

The worst post-observation value is 3, query cost is 1, and the net query value is 2 versus immediate value 1. The controller therefore chooses `acquireEvidence` with robust value of information +1.

## Assurance boundary

This is a one-step finite belief filter, not yet a complete POMDP. Transition dynamics, observation calibration, multi-step Bellman recursion, and statistical identification remain external. The query decision is worst-case over observations rather than probability-weighted and does not imply a real trade.
