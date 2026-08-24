# Certificate Composition Law

A proof-carrying research pipeline often contains several locally valid artifacts:

```text
signed dataset certificate
verified decision certificate
verified result certificate
```

It is tempting to conclude that three green certificates imply one green global research claim. That conclusion is unsound unless the certificates are bound to the **same objects in the same causal pipeline**.

## Global claim

For a dataset → decision → result pipeline, the global claim is:

```text
local dataset claim
∧ local decision claim
∧ local result claim
∧ dataset is the exact input consumed by the decision
∧ decision is the exact input evaluated by the result
```

The two final conjuncts are bridge claims. Local certificate validity does not imply them.

## Constructive counterexample

The controlled model contains four worlds:

- `matched` — all local certificates are valid and both bindings are correct;
- `datasetSubstituted` — each local certificate remains valid, but the decision consumed another dataset;
- `resultRelabeled` — each local certificate remains valid, but the result belongs to another decision;
- `bothSubstituted` — both cross-boundary bindings are wrong.

Every world produces the same local validity summary:

```text
dataset=pass, decision=pass, result=pass
```

Yet the global pipeline claim is true only in `matched`. Lean therefore carries an explicit evidence-equivalent counterexample proving that local pass/fail summaries cannot verify the global claim.

## Composition theorem

`certificate_composition_law` is the positive direction. If the three local claims and the two bridge claims are each verifiable from their corresponding observations, the combined evidence verifies their global conjunction.

This is not merely “put all files in one ZIP.” The bridge evidence must encode cross-object identity, for example:

```text
decision certificate contains dataset digest
result certificate contains decision digest
evaluation receipt binds result to the registered contract
```

## Exact bridge synthesis

The executable model exposes four candidate channels:

| Channel | Cost | Meaning |
|---|---:|---|
| `localValiditySummary` | 1 | only local pass/fail status |
| `dataDecisionBindingReceipt` | 2 | dataset digest bound into decision |
| `decisionResultBindingReceipt` | 2 | decision digest bound into result |
| `globalBundleBinding` | 6 | one integrated full-pipeline attestation |

The solver enumerates all 16 channel subsets. The exact minimum is:

```text
dataDecisionBindingReceipt
+ decisionResultBindingReceipt
cost = 4
```

The integrated global bundle also verifies the claim at cost 6. Every candidate below cost 4 carries a concrete world pair that it fails to distinguish.

## Why this matters

Without composition evidence, the following can all be true at once:

```text
dataset signature valid
decision proof valid
result certificate valid
global research claim false
```

This pattern applies beyond finance:

- software supply-chain attestations;
- ML training-data and model-evaluation certificates;
- experiment provenance;
- compliance workflows;
- multi-stage security analysis.

## Assurance boundary

The theorem proves composition relative to the declared local claims, binding claims, and observation maps. The exact solver is complete only over the four controlled worlds and four candidate channels.

The module does not establish that:

- the local certificate semantics are complete;
- a digest was measured at the correct causal boundary;
- the holder of a key is honest;
- external data or execution events are truthful;
- all cross-boundary substitution attacks are modeled.

A green global certificate is therefore only as strong as its local claims, bridge placement, trust domains, and history language.
