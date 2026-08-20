# Fragility-aware core/tactical allocation

This module formalizes a deliberately simple policy contract:

- 70 allocation units remain in a strategic risky-asset core;
- at most 30 units form a tactical overlay;
- stronger trend can increase the overlay;
- greater endogenous fragility cannot increase the overlay;
- a volatility-stress state can only cap or reduce exposure;
- the final target is always between 70 and 100 units;
- the rebalancing action buys below the target and sells above it.

The finite market state is estimated outside Lean from point-in-time data. A
proof-carrying `AllocationCertificate` then checks:

1. the claimed target equals the output of the formal policy;
2. the claimed buy/hold/sell action equals the deterministic rebalancing rule;
3. current and target allocations are unlevered;
4. the decision and state feature use no future information;
5. the state feature is bound to non-empty input and code hashes;
6. the policy hash matches the backtest decision parameter hash.

The proofs do **not** establish that 70/30 is universally optimal, that the
external state classifier is statistically correct, or that the policy is
profitable. Those are empirical claims requiring pre-registered out-of-sample
tests. Lean verifies the narrower safety, monotonicity, and provenance contract.
