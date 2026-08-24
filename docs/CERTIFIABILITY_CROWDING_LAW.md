# Certifiability–Crowding Law

This module formalizes and simulates a candidate investment principle:

```text
stronger evidence
→ higher allocator confidence
→ more allocated capital
→ greater crowding/impact cost
→ lower deployable alpha
```

The Lean theorem is structural. With a fixed economic alpha, nonnegative allocator response, and nonnegative impact coefficient, greater evidence confidence weakly increases allocation and weakly reduces deployable alpha. A zero-impact theorem shows that evidence alone does not reduce alpha; the effect requires a market-capacity channel.

## Controlled simulation

The deterministic fixture distinguishes three cases.

- `scalableValue`: the certifiable lower bound rises from 150 to 420 bps, allocation rises from 300 to 900 units, and deployable alpha falls from 425 to 275 bps.
- `limitedCapacitySignal`: the certifiable lower bound rises from 100 to 600 bps, but allocation rises from 200 to 800 units against only 500 units of strategy capacity. Deployable alpha falls from 380 to -580 bps.
- `zeroImpactBenchmark`: confidence and allocation increase, but deployable alpha remains 300 bps because the impact coefficient is zero.

The paradox is therefore not “proof destroys returns.” Evidence can improve knowledge while the induced allocation consumes a limited economic opportunity.

## Empirical status

The response equations and parameters are controlled inputs, not estimates. A real test requires dated improvements in strategy credibility or verification, subsequent allocator flows, capacity measures, transaction costs, and controls for publication, ordinary performance chasing, factor crowding, and market conditions.

The falsifiable prediction is that credibility shocks have a larger negative effect on subsequent deployable alpha when strategy capacity is low and market impact is high, while zero- or high-capacity strategies should show little decay from the allocation channel.
