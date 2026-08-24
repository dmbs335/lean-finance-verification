# Exact Evidence-Adjusted Portfolio Synthesis

Conventional finite selection ranks strategies by observed alpha after a conventional risk penalty. This benchmark adds four research-integrity dimensions:

- the lower endpoint of each certifiable alpha interval;
- evidence debt;
- evidence robustness;
- concentration in shared data, model, execution, or provider domains.

For a selected portfolio, the declared objective is:

```text
certifiable lower alpha
- conventional risk penalty
- evidence-debt penalty
+ robustness reward
- shared-domain concentration penalty
```

The weights are governance inputs, not estimated asset-pricing coefficients. The formal theorem proves only the structural consequence of a nonnegative declared dependency penalty: holding every other portfolio summary fixed, greater dependency concentration cannot improve this score.

## Controlled result

The raw objective chooses `vendorValue + vendorMomentum`: the pair has the largest observed alpha after conventional risk, but both depend on `vendor-a`, have larger evidence haircuts, weak robustness, and total evidence debt 8.

The evidence-adjusted objective chooses `independentTrend + independentQuality`. Its headline alpha is lower, but its certifiable lower bound is stronger, evidence debt is 2, robustness is 8, and it has no shared dependency domain. The declared evidence-adjusted score rises from 320 for the raw pair to 600 for the independent pair.

The solver enumerates all six two-strategy portfolios exactly and emits a complete score breakdown for every candidate. This demonstrates that return-based diversification and evidence-based diversification can select different portfolios. It does not establish that the supplied evidence weights are market prices or investor preferences.
