# Evidence Debt

Evidence debt is the minimum cost of an evidence selection that distinguishes every
bounded history pair on which an integrity claim changes truth value. A candidate
language may also be fundamentally insufficient; this is represented by `impossible`
rather than by an arbitrary large number.

```lean
inductive EvidenceDebt
  | finite (cost : Nat)
  | impossible
```

The order places every finite cost below impossibility.

## Proof-carrying debt

A finite certificate contains:

- a selected candidate;
- a proof that it verifies the bounded model;
- a proof that every verifying candidate has at least its cost.

An impossibility certificate proves that no candidate in the complete declared
language verifies the claim.

Thus a numeric optimizer result is not accepted as debt. The minimum or impossibility
must be independently checkable.

## Dual monotonicity

Two monotonicity laws are mechanized.

### Attack-history expansion

When observations, claims, channel costs, and the candidate language are fixed:

```text
H ⊆ H′  ⇒  Debt(H) ≤ Debt(H′)
```

Adding possible adversarial histories cannot make verification cheaper. A finite debt
may become `impossible` when the old channel language does not observe the new attack.

### Candidate-channel expansion

For a fixed history model:

```text
C ⊆ C′  ⇒  Debt(C′) ≤ Debt(C)
```

Adding evidence candidates cannot make the optimum worse and may restore finite
verification from an impossible language.

These are opposing forces in model refinement:

```text
new attack histories  → attack pressure
new evidence channels → sensor relief
```

For finite intermediate debts, the repository proves the balance identity:

```text
baseline + attackPressure
=
repaired + sensorRelief
```

## Cost-model-tampering result

The conservative image of the old workflow contains ten terminal histories. Its
six-channel language has minimum debt 6:

```text
selfReport
+ targetedReceipt_executeHiddenSweep
+ targetedReceipt_readFutureData
```

Adding the observed cost-model-tampering action expands the bounded model to 32
histories. No subset of the old six channels distinguishes the honest execution from
the control-plane mutation, so old-language debt becomes `impossible`.

Adding `targetedReceipt_tamperCostModel` restores finite verification. The new optimum
is:

```text
selfReport
+ targetedReceipt_executeHiddenSweep
+ targetedReceipt_readFutureData
+ targetedReceipt_tamperCostModel
```

with cost 8. Relative to the conservatively preserved baseline, the newly observed
attack contributes two units of finite marginal evidence debt after its sensor is
available.

This example separates three outcomes that a simple cost number would conflate:

1. attack model unchanged: finite debt 6;
2. attack added but observation language unchanged: impossible;
3. attack and targeted sensor both added: finite debt 8.

## Interpretation boundary

Debt is exact only for the declared bounded history model, candidate evidence language,
and cost function. The cost units are a policy input, not a discovered physical
constant. Subsequent work should model trust-domain compromise, privacy leakage, and
adaptive sensor failure as constraints rather than only scalar costs.
