# Action-Semantics Version Spaces

Observed traces rarely identify one unique workflow action semantics. A single successful transition can support several guards and effects that all reproduce the observation but permit different unobserved histories.

The repository therefore represents semantics refinement as a finite **version space** rather than immediately trusting one convenient action model.

## Finite hypothesis language

`LeanFinance/Epistemic/SemanticsVersionSpace.lean` defines a deterministic action hypothesis:

```lean
structure ActionSemanticsHypothesis (State) where
  enabled    : State → Bool
  transition : State → State
```

Positive observations provide a pre-state and observed post-state. Negative observations provide states where the action must be disabled.

A hypothesis belongs to the current version space exactly when it:

- enables every positive pre-state;
- reproduces every positive post-state;
- disables every negative probe state;
- belongs to the declared finite candidate language.

## Version-space contraction

Adding observations cannot add hypotheses:

```text
old observations ⊆ new observations
────────────────────────────────────
VersionSpace(new) ⊆ VersionSpace(old)
```

Lean proves this antitonicity separately for positive transitions and negative enablement probes.

This is the semantics-learning counterpart of Evidence Debt monotonicity:

- adding attacks expands verification obligations;
- adding observations contracts semantic ambiguity.

## Active instrumentation

Two currently consistent hypotheses may disagree on an unobserved state. `DistinguishingProbe` records:

```text
one probe state
left consistent hypothesis
right consistent hypothesis
proof that their enabled/next-state predictions differ
```

Such a state is a candidate controlled experiment or additional runtime instrumentation point.

## Cost-model tampering example

The observed transition is:

```text
before
  baselineExecuted  = true
  resultPublished   = false
  costModelTampered = false

after
  costModelTampered = true
```

Two negative probes establish that the action is disabled before baseline execution and after publication.

Exactly two conjunctive guards remain consistent:

```text
H₁
  baselineExecuted ∧ ¬resultPublished

H₂
  baselineExecuted ∧ ¬resultPublished ∧ ¬costModelTampered
```

The current trace does not determine whether the mutation can be invoked again once the cost model is already tampered.

The exact active-probe solver finds one distinguishing state:

```text
baselineExecuted  = true
resultPublished   = false
costModelTampered = true
```

At this state:

```text
H₁ predicts enabled
H₂ predicts disabled
```

The generated Lean witness proves that both hypotheses remain consistent and that the proposed probe separates them.

## Model-family evidence separation

`LeanFinance/Epistemic/ModelFamily.lean` lifts Evidence Separation from one fixed workflow to worlds of the form:

```text
(model, history)
```

A portfolio verifies a claim over a semantics version space only when every admissible pair of model/history worlds with different claim values is separated.

The repository proves:

- model-family cut-set duality;
- verification antitonicity under version-space expansion;
- constructive cross-model counterexamples;
- a point-model verification result may underestimate the evidence needed for the full family.

## Trust boundary

The finite solver currently uses:

- Boolean states;
- conjunctions of literals stable across positive observations;
- constant assignments to explicitly observed effect fields;
- exhaustive Boolean probe enumeration.

It does not infer arbitrary programs or claim that one trace identifies the real causal mechanism. Its output is the complete hypothesis set inside the declared finite language.

The next layer synthesizes evidence portfolios uniformly across all models remaining in this version space and then chooses the lowest-cost probe that most reduces robust Evidence Debt.
