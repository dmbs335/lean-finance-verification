# Proof-Carrying Formula Contract

A mathematically valid formula can still be applied incorrectly. Correct financial computation therefore requires a certificate for the **application**, not only a proof or reference for the expression.

## Formula versus application

The controlled contract separates seven claims:

```text
formula correctness
∧ domain preconditions
∧ unit signature
∧ temporal availability
∧ implementation identity
∧ input artifact binding
∧ output artifact binding
```

Examples of application failure include:

- dividing by a zero hedge-risk estimate;
- supplying currency where risk basis points are required;
- using an input published after the decision;
- executing code whose hash differs from the reviewed implementation;
- substituting another portfolio-risk artifact;
- relabeling the output of another invocation.

The formula itself can remain correct in every one of these worlds.

## Formula Application Composition Law

`LeanFinance/Formula/Contract.lean` proves the following positive direction:

> If expression correctness and each application obligation are separately verifiable from their corresponding evidence, the combined evidence verifies the global formula-application conjunction.

It also contains a constructive counterexample. A correct world and a unit-mismatched world expose the same formula-validity summary, while the global application claim differs. Therefore:

```text
FormulaCorrect(F)
↛ ApplicationCorrect(F, inputs, implementation, output)
```

## Controlled hedge-scale contract

The executable fixture registers:

```text
-(currentRisk / hedgeRisk) * (riskPercentage / 100)
```

with the unit signature:

```text
currentRisk      risk-bps
hedgeRisk        risk-bps
riskPercentage   percent
```

and `hedgeRisk` as the denominator input.

Seven application worlds are generated:

```text
correct
unitMismatch
futureInput
zeroDenominator
implementationDrift
inputSubstituted
outputRelabeled
```

The mathematical expression and expression hash are identical in every world. Each invalid world violates exactly one application dimension.

## Exact evidence synthesis

The candidate language contains eight channels:

| Channel | Purpose | Cost |
|---|---|---:|
| `formulaValiditySummary` | formula identifier and expression hash only | 1 |
| `unitSignatureReceipt` | registered units | 1 |
| `availabilityReceipt` | input cutoff | 1 |
| `domainReceipt` | denominator and other preconditions | 1 |
| `implementationReceipt` | executable implementation hash | 1 |
| `inputBindingReceipt` | exact consumed input artifacts | 1 |
| `outputBindingReceipt` | exact produced output artifact | 1 |
| `globalApplicationBinding` | integrated full invocation attestation | 8 |

The solver enumerates all 256 subsets. Formula validity alone cannot distinguish any application error. The exact minimum is the six narrow application receipts at total cost 6. The global application bundle also verifies the claim at cost 8.

Every candidate below cost 6 carries a concrete correct/incorrect world pair it fails to distinguish.

## Unit and scale semantics

A production contract should make the following differences explicit rather than relying on names or comments:

```text
decimal rate       0.03
percent             3
basis points      300
period return
annualized return
currency amount
price
risk sensitivity
volatility
```

Unit conversion is part of the certified transformation. A formula accepting `percent` does not automatically accept a decimal fraction, even when both values are represented by the same primitive numeric type.

## Temporal semantics

Every input carries `available_at`, and the application decision carries a cutoff. The availability receipt proves:

```text
available_at(input_i) ≤ decision_at
```

for every consumed input. A source timestamp, observation date, publication date, and receipt date may differ; the contract must identify which one determines admissibility.

## Domain and approximation semantics

Domain conditions are executable obligations, not prose. Examples include:

```text
denominator ≠ 0
volatility ≥ 0
correlation ∈ [-1, 1]
probability ∈ [0, 1]
positive-definite covariance matrix
nonempty calibration window
nonoverlapping return intervals
```

Approximate formulas should additionally carry a tolerance or residual bound. A numerically closed identity without an error bound does not establish that an approximation is adequate for the claimed use.

## Commands

```bash
python -m tools.formula_contract analyze \
  --model examples/formula_contract/hedge_scale.json \
  --out /tmp/formula-contract.json

python -m tools.formula_contract verify \
  --model examples/formula_contract/hedge_scale.json \
  --report /tmp/formula-contract.json
```

## Relationship to certificate composition

Certificate Composition binds local research stages into one causal pipeline. Formula Contract applies the same principle inside a calculation:

```text
formula
→ implementation
→ input artifacts
→ invocation
→ output artifact
```

Local validity at each node does not establish that the nodes belong to the same invocation. The bridge receipts supply that identity.

## Assurance boundary

The formal theorem is relative to the declared claims and observation maps. The exact solver is complete only over the seven controlled worlds and eight candidate channels.

It does not establish that:

- the mathematical formula is appropriate for the economic problem;
- the registered units accurately describe external data;
- the implementation hash was measured on the deployed binary;
- the input artifacts are truthful merely because their identifiers match;
- all domain failures or numerical instabilities are represented;
- a valid formula application implies a profitable investment decision.
