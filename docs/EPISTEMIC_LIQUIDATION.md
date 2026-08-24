# Epistemic Liquidation Dynamics

Traditional crowding measures focus on common positions, factors, leverage, and liquidity exits. This model adds a different dependency: two strategies can have low historical return correlation while relying on the same data vendor, model pipeline, execution path, or evidence provider.

A common methodology or evidence failure can then produce the following chain without a new fundamental cash-flow shock:

```text
shared research dependency fails
        ↓
certifiability or evidence confidence falls
        ↓
allocator capital is reduced
        ↓
multiple strategies liquidate
        ↓
shared assets absorb selling pressure
        ↓
tail correlation and price impact rise
```

## Formal boundary

`EvidenceConfidenceShock` records confidence and capital before and after a methodology event. `AllocationRespondsToEvidenceShock` is an explicit causal assumption: confidence falls and the allocator reduces capital. Lean proves that this assumption entails positive liquidation pressure.

`SharedEvidenceShock` carries the same response assumption for two strategies. Lean then proves synchronized and positive aggregate liquidation. No return-correlation premise is required. This establishes the logical mechanism, not its empirical prevalence.

## Deterministic scenario

The checked-in scenario contains three strategies.

- `momentumAlpha` and `valueAlpha` have only 300 basis points of declared return correlation but share `vendorA` and `engineX`.
- `defensiveBeta` uses an independent vendor and engine.

A `vendorA` revision failure causes both low-correlation alpha strategies to reduce capital and sell assets, while the independent strategy is unaffected. A `vendorB` failure produces the opposite pattern. Asset impact is a deterministic liquidity-scaled illustration rather than a calibrated market-impact estimate.

## Testable hypotheses

The model yields empirical hypotheses rather than an established market law:

1. Evidence-dependency overlap predicts simultaneous capital withdrawals after methodology shocks, conditional on position and factor overlap.
2. Low-return-correlation strategies can exhibit high tail dependence when their research validity relies on the same provider or pipeline.
3. Diversifying data, execution, and evidence trust domains reduces liquidation correlation even when the trading signals remain unchanged.
4. Methodology shocks can create transient price pressure without contemporaneous fundamental news.

Testing these claims requires real manager dependency graphs, allocator flows, methodology incidents, and position/liquidity data. The synthetic example only demonstrates that the mechanism is coherent and executable.
