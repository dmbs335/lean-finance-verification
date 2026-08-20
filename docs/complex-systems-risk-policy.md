# Complex-systems risk policy verification

This module verifies the execution contract around a deliberately simple
core/tactical policy:

- 70 allocation units remain in a strategic risky-asset core;
- at most 30 units form a tactical overlay;
- weaker trend cannot increase exposure;
- greater endogenous fragility cannot increase exposure;
- volatility stress acts only as an exposure cap;
- the final risky-asset target remains between 70 and 100 units;
- current exposure below the target yields `buy`, above it yields `sell`, and an
  exact match yields `hold`.

The finite market state is estimated outside Lean. A proof-carrying
`AllocationCertificate` checks that:

1. the claimed target equals the deterministic policy output;
2. the claimed buy/hold/sell action matches current and target exposure;
3. current and target allocations remain unlevered;
4. the associated `Backtest.Decision` uses no future information;
5. the state feature appears in that decision and is bound to non-empty input
   and code hashes;
6. decision time and policy hash agree with the claim.

This layer is intentionally complementary to a signal-estimation or portfolio
selection model. It does **not** prove that 70/30 is universally optimal, that
an external trend or fragility classifier is statistically correct, or that the
policy is profitable. Those claims require pre-registered out-of-sample tests.
Lean verifies the narrower safety, monotonicity, action, and provenance
contract.
