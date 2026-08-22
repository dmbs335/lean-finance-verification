# Conservative Workflow Model Refinement

Observed attack traces can reveal actions absent from a finite workflow model. Adding
an action is useful only if the extension does not silently reinterpret the workflow
that was already accepted.

`LeanFinance/Epistemic/ModelRefinement.lean` defines a conservative embedding between
an original and refined workflow. The contract requires:

- an injective embedding of every original action;
- inclusion of every embedded action in the refined alphabet;
- preservation of the initial state;
- preservation of action enablement on every embedded state and action prefix;
- commutation of transitions with the state embedding;
- preservation of terminal classification;
- preservation of the old integrity claim;
- preservation of an arbitrary state-derived observation.

The central replay theorem is:

```lean
replay refined (trace.map embedAction)
=
Option.map embedState (replay original trace)
```

It applies to every original trace, not only the trace used to infer the new action.
Consequences include:

```text
old successful trace  → same embedded final state
old failed trace      → still fails
old terminal trace    → same terminal classification
old claim value       → unchanged
old state evidence    → unchanged
```

## Cost-model tampering instance

The observed-trace refinement adds:

```text
state  costModelTampered : Bool = false
action tamperCostModel
effect costModelTampered := true
claim  ¬costModelTampered
```

The concrete witness embeds every original state by setting the new bit to `false`,
embeds all six original actions, and mechanically proves the workflow contract.
Consequently, the refined 32-history model can explain the new control-plane attack
without changing any prior replay, claim, or legacy state observation.

This separates two obligations that were previously bundled together:

1. **explanatory extension** — the new model can replay the observed attack;
2. **conservative preservation** — all previously expressible behavior retains its
   old semantics.

A trace-refinement certificate without the second property may fit the new example by
changing old rules. A conservative refinement cannot.

## Boundary

The theorem establishes a forward simulation for the embedded original action
alphabet. It does not say that every refined action has an original counterpart, nor
does it prove that one observed trace uniquely determines the new action's global
semantics. Those questions belong to action-schema version spaces and robust
model-family synthesis.
