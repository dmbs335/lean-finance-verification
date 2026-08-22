# Observation Boundary Theorem

Evidence strength and evidence location are different properties. A cryptographically strong artifact created downstream of a visibility boundary may authenticate the visible record perfectly while revealing nothing about an upstream action that never crossed that boundary.

## Factorization

An evidence map factors through a boundary when:

```text
history
  ↓ boundary
boundary state
  ↓ deterministic downstream processing
final evidence
```

Formally:

```lean
FactorsThroughBoundary boundary evidence :=
  ∃ downstream,
    ∀ history,
      evidence history = downstream (boundary history)
```

Factorization is transitive. If an execution report factors through a publication boundary and a timestamp factors through that report, the timestamp also factors through the publication boundary.

## Downstream impossibility

The main theorem states:

```text
claim not verifiable from boundary
+
evidence factors through boundary
─────────────────────────────────
claim not verifiable from evidence
```

A stronger constructive form needs only two histories:

```text
boundary(honest) = boundary(attack)
claim(honest) ≠ claim(attack)
```

Every downstream evidence map that factors through that boundary assigns equal evidence to the pair and therefore cannot verify the claim.

## Channel-family form

A selected channel family factors through a common boundary when every selected channel has a boundary-state decoder. If two histories have the same boundary state, all selected channel observations agree.

Consequently, no such selected family verifies a claim that changes truth value across the pair.

This is the workflow-level interpretation of verification non-amplification:

> Downstream evidence cannot recover an upstream distinction that never entered the shared observation boundary.

## Cryptographic consequence

The result is independent of the downstream transformation. It applies to:

- hashes;
- canonical serialization;
- digital signatures;
- RFC 3161 timestamps;
- transparency-log inclusion proofs;
- generated reports;
- Lean proof terms whose premises contain only the factorized evidence.

These mechanisms remain essential for integrity, existence time, and non-equivocation claims. They simply cannot prove a different claim about an event omitted before their input boundary.

## Cost-model tampering interpretation

In the observed control-plane mutation fixture:

```text
honest execution
cost-model-tampered execution
```

produce the same researcher-visible declaration, selected result bundle, timestamped ledger, and existing execution-log projection. Their distinction appears only at the cost-model mutation boundary. Therefore the new targeted mutation receipt is not merely another convenient sensor; it crosses a causal boundary that all prior evidence factored through or bypassed.

## Next theorem

The next refinement is transition-level:

```text
all reachable first-violation transitions
must be covered by a persistent and specific observation channel
```

Under suitable no-erasure assumptions, this should replace terminal-history-pair enumeration with a transition-level safety–observability duality.
