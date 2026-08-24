# Off-Policy Authority Monitor

This layer turns logged shadow decisions into a bounded authority decision without pretending that one historical backtest is sufficient for autonomy.

## Doubly-robust arithmetic

For each logged one-step decision, the executable estimator computes:

```text
target-model value
+ (target probability / behavior probability)
  × (realized reward - logged-action model value)
```

All calculations use exact rational arithmetic. The controlled four-record fixture produces a doubly-robust target value of `57/8 = 7.125` bps. Against a baseline value of 2 bps, the exact improvement estimate is `41/8 = 5.125` bps.

A declared confidence radius of 2 bps yields the conservative integer envelope `[3, 8]`. This clears the registered 2 bps promotion margin.

## Effective sample size

Importance weights can make a large log behave like a tiny sample. The monitor therefore checks:

```text
ESS = (Σw)² / Σw²
```

The fixture has exact ESS `49/15 ≈ 3.27`, clearing the registered minimum 3. A counterfactual with one extreme importance weight drives ESS below the threshold and holds authority at `recommend` even though the point estimate is positive.

## Anytime authority rule

The monitor advances exactly one authority level only when all gates pass:

- improvement lower bound clears its registered margin;
- ESS reaches its minimum;
- risk upper bound is within budget;
- no model shift is detected;
- no operational breach is active.

The controlled result advances `recommend → microAutonomy` with a cap of 10 units. A model-shift counterfactual revokes immediately.

## Assurance boundary

Lean checks interval ordering, cross-multiplied ESS arithmetic, registered lower-bound and risk gates, and the resulting authority transition. Python recomputes the exact rational estimator and report.

The statistical coverage of the confidence radius, optional-stopping validity, correctness of behavior probabilities, model adequacy, and causal interpretation remain external assumptions. A future layer should import independently generated confidence-sequence certificates rather than treating the radius as a governance input.
