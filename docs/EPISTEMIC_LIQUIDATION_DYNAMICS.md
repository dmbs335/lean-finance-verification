# Epistemic Liquidation Dynamics

This module studies a controlled mechanism rather than claiming an established empirical market law:

```text
shared evidence-domain failure
→ confidence loss
→ capital withdrawal
→ price impact
→ mark-to-market loss
→ margin/funding withdrawal
```

Two strategies can have low historical return correlation while depending on the same data vendor, model pipeline, execution environment, or evidence provider. A failure at that shared research boundary can therefore synchronize their first-round withdrawals even when conventional return correlation suggests diversification.

## Latent overlap versus realized shock

The consolidated report distinguishes two states that were previously easy to conflate.

### Hidden epistemic crowding

```text
low return correlation
+ at least one shared research-validity dependency
```

This is a latent common-risk path even when no provider has failed and no capital has moved. The report includes the shared domains and a Jaccard-style dependency-overlap score in basis points.

### Hidden common liquidation risk

```text
hidden epistemic crowding
+ a shared dependency actually fails
+ both strategies withdraw in the first round
```

Removing the `vendor-a` shock therefore eliminates synchronized liquidation and market impact while leaving the underlying dependency overlap visible. This makes the causal origin of the stress scenario explicit.

The checked-in scenario shocks `vendor-a`. `globalValue` and `usMomentum` have only 200 bps of scaled return correlation but both withdraw because the failed vendor is part of their evidence dependency. `independentTrend` uses another vendor and has no first-round evidence withdrawal, although it can still suffer second-round market-impact and margin contagion.

The simulator is intentionally transparent and integer-valued. Evidence withdrawal rates are declared per dependency, market impact is linear in exposure-weighted withdrawal relative to market liquidity, and margin withdrawal is linear in losses above a strategy-specific buffer. These equations are not calibrated estimates of real markets.

The model yields falsifiable hypotheses for later empirical work:

1. methodology or vendor shocks should create synchronized outflows among low-return-correlation strategies sharing the affected evidence domain;
2. independent strategies can still be harmed through price-impact contagion;
3. evidence-dependency overlap should predict part of tail co-movement beyond holdings, factor, and return overlap;
4. latent dependency overlap should remain measurable before the incident, while realized common liquidation should appear only after the shared-domain shock.

A real test requires strategy-level dependency data, dated methodology/vendor incidents, flows or position changes, and controls for ordinary factor and liquidity crowding.
