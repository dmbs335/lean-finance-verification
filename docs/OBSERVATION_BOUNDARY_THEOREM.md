# Observation Boundary Theorem

Evidence strength and evidence location are different properties. A cryptographically
strong artifact generated after an observation boundary cannot recover a distinction
that never crossed that boundary.

Let:

```text
boundary : History → BoundaryState
evidence : History → Evidence
```

Evidence factors through the boundary when there is a deterministic function `f` such
that:

```text
evidence(history) = f(boundary(history))
```

The repository proves:

```text
Verifiable(evidence, claim)
→ Verifiable(boundary, claim)
```

and its impossibility form:

```text
¬ Verifiable(boundary, claim)
→ FactorsThroughBoundary(boundary, evidence)
→ ¬ Verifiable(evidence, claim)
```

This is the workflow-location form of verification non-amplification.

## Channel-family theorem

The result also applies to a selected family of evidence channels. If every selected
channel factors through one boundary and two histories have equal boundary states but
different claim values, no selected channel combination verifies the claim.

```text
same boundary
+ claim disagreement
+ all selected channels factor through boundary
⇒ selected channel family cannot verify
```

The conclusion is independent of downstream hashing, canonical serialization,
digital signatures, timestamps, proof terms, or report generation.

## Cost-model-tampering instance

The visible publication boundary contains:

```text
researcher-visible declaration
selected result bundle
RFC 3161 timestamp over the visible ledger
```

The honest execution and the cost-model-tampering execution produce the same visible
boundary state but have different integrity claims. Hidden parameter sweeps and
future-data access are boundary-silent as well.

Lean proves that:

- the result-bundle observation factors through the boundary;
- the RFC 3161 timestamp observation factors through the boundary;
- the self-report factors through the boundary;
- no deterministic post-processing of the complete boundary can certify the upstream
  integrity claim;
- the entire declaration/result/timestamp channel family cannot certify it.

The limitation is causal rather than cryptographic. RFC 3161 correctly proves when the
visible ledger existed. It does not prove that every relevant execution, data access,
or control-plane mutation entered that ledger.

## Design consequence

To verify an upstream distinction, evidence must be generated at or before a boundary
where that distinction is still observable. In the current examples:

```text
hidden parameter sweep  → execution receipt
future-data access       → data-access receipt
cost-model mutation      → control-plane mutation receipt
```

Adding a stronger downstream signature does not substitute for moving the observation
boundary upstream.

## Boundary

Factorization is a semantic modeling claim. A real implementation must justify that a
channel truly depends only on the declared boundary state and that no independent
upstream side channel is present. The theorem does not weaken cryptographic integrity;
it states precisely which historical distinctions cryptographic protection can and
cannot preserve.
