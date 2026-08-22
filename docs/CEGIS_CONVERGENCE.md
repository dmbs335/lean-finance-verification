# Finite CEGIS Convergence

The workflow synthesizer already emits proof-carrying counterexample rounds, but a connected transcript alone does not explain why refinement must terminate or why the final repair is globally optimal.

`LeanFinance/Epistemic/CEGISConvergence.lean` isolates the finite convergence argument from any particular workflow representation.

## Constraint problem

A finite synthesis problem contains:

```text
constraints : List Constraint
satisfies   : Candidate → Constraint → Prop
cost        : Candidate → Nat
```

A constraint may represent:

- a terminal history-pair separator edge;
- a first-violation transition class;
- one channel-failure scenario;
- one trust-domain-failure scenario;
- a conjunction of attack and fault obligations.

## Exact master

`ExactMasterResult problem known selected` proves:

```text
selected satisfies every known constraint
and
selected has minimum cost among all candidates satisfying the known constraints
```

The definition does not trust an optimizer-reported objective. A generated certificate must provide the semantic lower bound.

## Complete oracle

A valid oracle outcome is either:

```text
verified
  selected satisfies every declared finite constraint

counterexample c
  c belongs to the declared universe
  selected fails c
```

One `ConstraintCEGISRound` combines an exact master result with a fresh oracle counterexample and proves that the discovered-constraint list grows by exactly one.

## Finite progress measure

`StrictlyDecreasingMeasures` records a natural-number measure after every counterexample round. The intended instance is the number of undiscovered finite constraints.

Lean proves:

```text
number of rounds ≤ initial measure
```

Therefore a run cannot produce more fresh counterexamples than the finite obligation universe permits.

## Global soundness and optimality

A `ConvergedCEGISCertificate` contains:

- the final discovered constraints;
- proof that they belong to the declared finite problem;
- an exact final master result;
- a complete `verified` oracle result;
- a strictly decreasing finite progress transcript.

The repository proves:

```text
final candidate satisfies every finite constraint
```

and:

```text
for every globally feasible candidate,
  final cost ≤ candidate cost
```

The optimality proof is simple but important. Every globally feasible candidate satisfies the final master's discovered subset, so exact master optimality already lower-bounds every globally feasible alternative.

## Relation to the executable engine

The current Python CEGIS engine can instantiate:

```text
Constraint = disagreement edge
measure    = total edges - discovered edges
```

The transition-level backend can instead instantiate:

```text
Constraint = first-violation transition class
measure    = uncovered transition classes
```

Both share the same convergence and optimality theorem. The remaining implementation step is to emit these generic certificate objects directly from the executable transcripts rather than checking only the final finite candidate table.
