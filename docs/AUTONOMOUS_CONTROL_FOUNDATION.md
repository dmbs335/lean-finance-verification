# Proof-Carrying Autonomous Control Foundation

This module is the first closed-loop control layer for an autonomous investment harness. The advanced controller remains untrusted. A small verified boundary decides whether its proposal is admissible, replaces unsafe proposals with a total baseline fallback, restricts policy improvement to sufficiently supported state-action pairs, and advances authority only through a registered evidence gate.

## Mathematical objects

A finite-support controlled model contains states, actions, and every represented successor of each state-action pair. For a declared safe set `K`, an action is robustly safe when:

```text
all listed successors of (state, action) are in K
```

The finite-horizon viability kernel is defined recursively:

```text
K₀ = K
Kₜ₊₁ = {s ∈ K | some action keeps every successor in Kₜ}
```

A runtime shield applies an advanced proposal only when its trusted Boolean checker accepts it; otherwise it emits a registered fallback. Lean proves every shield output is accepted by that checker.

## Baseline-constrained improvement

A deterministic candidate follows the SPIBB-style restriction:

```text
if the candidate action has fewer than N_min logged observations,
the candidate must equal the trusted baseline at that state
```

The exact Python analyzer computes the viability layers, safe action set, shielded proposal, supported candidate policy, and a controlled pessimistic score. A policy certificate carries the arithmetic proposition:

```text
candidate lower score ≥ baseline lower score + registered margin
```

The fixture has a baseline score of 2 and candidate score of 8, clearing the registered margin 5. `increase` is retained in `normal`, but unsafe or unsupported increases in `stressed` and `margin` are replaced by `reduce`.

## Authority governor

The authority ladder is:

```text
observe → shadow → recommend → microAutonomy → boundedAutonomy
```

`fallback` and `revoked` are emergency states. A model shift or operational breach revokes immediately. Otherwise a candidate advances exactly one level only when:

- the registered policy-improvement gate passed;
- improvement lower bound is positive;
- effective sample size reaches its minimum;
- risk upper bound is within budget.

In the controlled fixture, `recommend` advances to `microAutonomy` with a capital cap of 10 units. These caps are governance inputs, not an investment recommendation.

## Assurance boundary

The results are exact over the declared finite states, actions, successor supports, support counts, lower-bound scores, and thresholds. The module does not establish calibrated transition probabilities, statistical coverage of the supplied lower bounds, future profitability, or real-market safety. Those obligations motivate the next statistics and robust-control layers.
