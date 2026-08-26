# Evidence-Conditioned Robust Control

This layer turns the repository's evidence-version-space idea into a control algorithm. The current evidence state determines a finite ambiguity set of models. Immediate actions are evaluated by their worst represented net value:

```text
robust value(action, models)
= min model value - execution cost
```

Stronger evidence removes models. Lean proves that the greatest robust lower bound cannot decrease under set refinement.

## Evidence acquisition is an action

The controller can trade now or acquire another independent observation. For a query `q`, the robust post-query guarantee is:

```text
min over possible observations
  max action
    min remaining model value
```

The robust value of information is that guarantee minus query cost and current robust value. The controlled ambiguity set contains `bear`, `base`, and `bull` models. Without another observation, `hold` has robust value 1 bps.

`independentMacro` splits the ambiguity set. Under `stable`, the robust action becomes `increase` at 7 bps; under `stress`, it becomes `reduce` at 4 bps. The worst post-query value is 4, query cost is 1, and net value is 3. Robust value of information is therefore +2, so the controller chooses `acquireEvidence` rather than trade immediately.

A redundant `sameVendor` query leaves all models possible, costs 1, and has value of information -1.

## Certifiability gain versus crowding cost

Evidence does not automatically justify more capital. The capital gate is:

```text
robust value gain > incremental crowding cost
```

The fixture has robust gain 2 and crowding increase 1, so controlled expansion is allowed. Raising incremental crowding to 4 blocks expansion even though evidence still improves model discrimination.

## Assurance boundary

The model family, model-specific values, observation branches, evidence costs, and crowding costs are controlled inputs. No observation probabilities, transition calibration, or real-market causal claim is made. The exact result is a robust finite decision contract, not an investment recommendation.
