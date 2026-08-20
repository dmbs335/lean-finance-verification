# Dynamic Bottleneck Verification

This module turns a minimal industrial-bottleneck model into machine-checkable
claims without pretending that Lean can certify unobserved empirical facts.

## Formalized boundary

A `SupplyNode` separates:

- topology (`TopologySignature`),
- incumbent capacity,
- demand-to-flow intensity,
- announced additions gated by completion and qualification,
- alternate capacity gated by physical readiness, qualification, switching,
  and IP compatibility.

At time `t`, a node is a capacity bottleneck exactly when

```text
effectiveCapacityAt node t < requiredFlow node finalDemand
```

The effective-capacity calculation excludes announced but unqualified projects
and technically incompatible alternates.

## Verified claims

The current Lean proofs establish:

1. a ready project contributes its units, while a non-ready project contributes
   zero;
2. an IP-incompatible alternate contributes zero;
3. capacity sufficiency rules out a capacity bottleneck and forces computed
   scarcity units to zero;
4. the first-node scan is sound: every returned ID corresponds to an actual
   binding node in the supplied process order;
5. identical topology can coexist with opposite bottleneck states, so topology
   or centrality alone cannot determine scarcity;
6. zero duration, zero bargaining capture, zero ownership, or full market
   pricing eliminates the corresponding dynamic-rent or investable score;
7. a `DynamicBottleneckCertificate` carries both the binding proof and the
   existing point-in-time `NoFutureInformation` guarantee over datasets and
   feature lineage.

The examples include a qualification-delayed HBM-style capacity addition, a
regulated-shortage zero-capture case, a fully priced scarcity case, and an
ample-capacity battery-style negative control.

## Trust boundary

Lean verifies implications from supplied observations. It does not prove that
reported capacity, qualification dates, final demand, bargaining weights, or
ownership weights match the external world. Those values require signed,
point-in-time data lineage and independent empirical adapters.

The present model is deliberately local. A full Dynamic Bottleneck Score still
requires network-wide multi-commodity optimization, shared-alternate-capacity
allocation, common-failure domains, endogenous CAPEX and yield ramps, and a
formal connection between optimization dual values and bilateral bargaining.
