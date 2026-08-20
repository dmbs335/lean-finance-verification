# Inverse-Game Identification

The inverse problem is not defined as “recover every hidden payoff exactly.”
It is defined relative to an observation map and a prediction target.

For latent state `theta`, public observation `observe theta`, and target
`target theta`, the target is point identified when

```text
observe theta_1 = observe theta_2
  -> target theta_1 = target theta_2
```

This repository formalizes three useful results:

1. `identified_of_factorization`: a target is identified when it can be decoded
   from the public observation.
2. `identified_postprocess`: deterministic post-processing preserves
   identification.
3. `not_identified_of_counterexample`: two observationally equivalent states
   with different targets constructively refute identification.

`hiddenPayoff_not_identified_by_coarseObservation` gives a concrete inverse-game
counterexample: the same aggregate-flow bucket is compatible with distinct
payoff types. In contrast,
`constraintBinding_identified_by_enrichedObservation` shows that a binding
constraint is identifiable once the observation contains a valid constraint
proxy.

The practical implication is to estimate equivalence-class invariants such as
forced-flow direction, constraint activation, or transition risk, rather than
claiming unique recovery of every investor’s primitive utility and position.
