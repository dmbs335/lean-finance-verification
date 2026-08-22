# Evidence Debt

Evidence Separation Theory determines whether an integrity claim is constant on the equivalence classes induced by preserved evidence. **Evidence Debt** adds an optimization layer:

> What is the minimum cost of an admissible evidence portfolio that verifies the claim over the declared adversarial model?

`LeanFinance/Epistemic/EvidenceDebt.lean` represents an optimum with a proof-carrying witness rather than trusting an external optimizer's scalar answer.

## Proof-carrying optimum

For a bounded model `model` and explicit candidate portfolio language `candidates`, an `EvidenceDebtWitness model candidates` contains:

```text
selected portfolio
selected ∈ candidates
selected verifies the model
no verifying candidate has lower cost
```

Its debt is `selectionCost model selected`.

The candidate language is explicit because two independent changes affect debt in opposite directions:

- expanding the adversarial history model creates new verification obligations;
- expanding the available sensor language creates new ways to satisfy those obligations.

## Attack-pressure monotonicity

Suppose a large model conservatively extends a small model:

```text
small histories ⊆ large histories
claims agree on all old histories
old channels retain their observations
old channels retain their costs
```

Then every portfolio that verifies the large model also verifies the small model. For the same candidate portfolio language:

```text
minimumDebt(small) ≤ minimumDebt(large)
```

A newly admitted attack cannot make an existing verification problem cheaper when no new sensor is introduced.

## Sensor-relief antitonicity

For one fixed adversarial model, if the admissible portfolio language grows:

```text
oldCandidates ⊆ newCandidates
```

then:

```text
minimumDebt(newCandidates) ≤ minimumDebt(oldCandidates)
```

A new receipt, attestation, or independent provider may reduce cost because it can dominate a broader or more privacy-invasive channel.

## Debt balance

Let:

```text
baseDebt      minimum cost before the attack-model extension
expandedDebt  minimum cost after adding attacks, with the old sensors
repairedDebt  minimum cost after also adding new sensors
```

Define:

```text
attackPressure = expandedDebt - baseDebt
sensorRelief   = expandedDebt - repairedDebt
```

Under the two monotonicity results:

```text
baseDebt + attackPressure
=
repairedDebt + sensorRelief
```

Both sides equal the debt of the expanded attack model under the old sensor language. This separates a genuine new adversarial obligation from the cost recovered by improved instrumentation.

## Interpretation

Evidence Debt is always relative to:

- a history or transition model;
- a claim;
- evidence-channel semantics;
- a candidate portfolio language;
- a cost function.

It is not a universal number attached to an attack name. A new trace may raise debt in one workflow, leave it unchanged in another because an existing channel already separates it, or expose that no finite debt exists in the current channel language.

The next layer will generalize scalar debt to **Epistemic Connectivity**: the minimum number of independent channel or trust-domain failures required to make a verified claim unverifiable.
