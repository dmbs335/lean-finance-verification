# Evidence-Obligation Taxonomy

Conventional attack taxonomies classify manipulations by implementation technique: hidden parameter search, future-data access, benchmark switching, cost-model tampering, and so on. Evidence Separation suggests a different classification:

> Which evidence portfolios distinguish the attack from every relevant honest history?

## Attack coverage

For a selected channel family `S`, `CoversAttack S attack` means that every designated honest history with the opposite claim truth value is separated from the attack by at least one channel in `S`.

This produces an evidence obligation independently of the attack's human-readable name.

## Subsumption

Attack `A` evidence-subsumes attack `B` when every portfolio covering `A` also covers `B`.

```text
A stronger than B
⇔
cover(A) ⊆ cover(B)
```

Subsumption identifies attacks whose evidence requirements are nested even when their execution traces differ.

## Equivalence

Two attacks are evidence-obligation equivalent when every selected portfolio covers one exactly when it covers the other.

```lean
EvidenceObligationEquivalent A B :=
  ∀ selected,
    CoversAttack selected A ↔
      CoversAttack selected B
```

The repository proves that this is mutual subsumption and establishes reflexivity, symmetry, and transitivity.

## Separator signatures

`SameSeparatorSignature A B` is a stronger, pointwise criterion. Relative to every honest baseline it requires:

- the same claim-disagreement relation;
- the same separating channels.

Equal signatures imply obligation equivalence. The converse need not be used as a definition because different separator hypergraphs can induce the same family of hitting sets.

## Constructive novelty

`EvidenceObligationCounterexample A B` supplies one selected portfolio that covers `A` but not `B`. It is a machine-checkable witness that the attacks are in different epistemic classes.

A second lower-bound rule proves that one honest baseline with a unique separator makes that channel necessary for the attack's complete obligation. This captures the `costModelTampering` result: the new control-plane mutation was invisible to the result bundle, RFC 3161 anchor, and existing execution log, so its targeted mutation receipt represented a new evidence boundary.

## Novelty criterion

A trace is `EvidenceNovelAgainst catalog attack` when it is obligation-inequivalent to every known catalog entry.

This supports a stricter automatic research-topic filter:

```text
new implementation instance only
  same evidence obligation as an existing class

new combination
  new conjunction of known separator obligations

new epistemic class
  requires a separator boundary not represented by any existing class
```

The next executable layer will compute canonical separator hypergraphs from the attack corpus, quotient traces by obligation equivalence, derive subsumption relations, and rank new traces by marginal Evidence Debt and connectivity loss.
