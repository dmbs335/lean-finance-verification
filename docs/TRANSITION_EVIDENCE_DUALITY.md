# Transition-Level Safety–Observability Duality

History-level Evidence Separation is exact, but its naive implementation compares terminal histories pairwise. Workflow histories grow exponentially with depth and independent attack actions.

A more structural question is:

> Which transitions first create a claim violation, and which persistent evidence channels cover those transition classes?

## Transition evidence system

`TransitionEvidenceSystem` separates five concepts:

```text
claim(history)
occurs(transition, history)
detects(channel, transition)
observe(channel, history)
violationComplete
```

Two semantic assumptions connect a transition detector to final evidence:

### Persistence

If a violating transition occurs and a channel detects it, the channel's final history observation is true.

```text
occurs(t, h) ∧ detects(c, t)
→ observe(c, h) = true
```

### Specificity

A channel detecting transition class `t` is absent from every claim-satisfying history.

```text
claim(h) = true ∧ detects(c, t)
→ observe(c, h) = false
```

These conditions exclude erasable receipts and false-positive detectors from the sufficiency theorem.

## Persistent transition-cover sufficiency

A selected evidence family covers violation transitions when every declared transition class has at least one selected detector.

The repository proves:

```text
all violation histories contain a declared violation transition
+
receipts are persistent and specific
+
selected channels cover every transition class
────────────────────────────────────────────
selected channels verify the terminal claim
```

This replaces an arbitrary number of attack histories with a potentially much smaller transition basis.

## Necessity and witness normal form

Transition coverage is not automatically necessary. Two transition classes might always occur together or one channel may separate their histories without being interpreted as a detector for either class.

`TransitionWitnessComplete` supplies the normal-form condition needed for necessity. Every transition class must have an honest/attack pair such that every channel separating that pair detects the transition.

Under that condition:

```lean
ChannelSelectionVerifies observe selected claim
↔
CoversViolationTransitions system selected
```

This is the transition-level safety–observability duality.

## Silent-violation impossibility

`SilentViolationWitness` gives the complementary lower bound:

```text
attack contains a declared violation transition
claim(honest) ≠ claim(attack)
all selected final observations agree
```

Then the selected family cannot verify the claim.

This generalizes the hidden-sweep, future-data, and cost-model-tampering examples. A violation transition that is silent at every selected evidence boundary remains unverifiable regardless of downstream hashing, signing, timestamping, or proof generation.

## Algorithmic consequence

The existing exact engine constructs hyperedges from terminal history pairs. Under a valid transition witness basis, a new backend can instead construct one evidence-cover constraint per reachable first-violation transition class:

```text
history-pair solver
  potentially quadratic in terminal histories

transition-cover solver
  one constraint per violation-transition class
```

The next empirical step is to extract first-violation transition classes from the generated workflow graph and compare the transition-cover optimum with the existing history-pair optimum on the 32-history cost-model-tampering model.
