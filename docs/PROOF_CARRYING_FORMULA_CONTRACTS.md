# Proof-Carrying Financial Formula Contracts

A mathematically correct formula can still be applied incorrectly. Financial calculation validity therefore has at least two layers:

```text
formula definition correctness
application correctness at one causal boundary
```

For the controlled hedge scaling formula:

```text
scale = -(currentRisk / hedgeRisk) × riskPercentage / 100
```

the formula text and final number do not establish that:

- the formula and implementation were registered before use;
- both risk values were available by the decision time;
- the risks have compatible units and currency;
- the values use the same valuation time;
- the values use the same risk-model version;
- the hedge denominator is nonzero;
- the input artifacts are the exact objects consumed;
- the output artifact existed by the decision;
- the reported rational result belongs to those exact inputs.

## Lean contract

`LeanFinance/Formula/Contract.lean` separates a registered `FormulaDefinition` from one `HedgeScaleApplication`. A valid application carries proofs of:

```text
definition and implementation hash match
formula preregistration
input availability
nonfuture valuation timestamps
output availability
unit compatibility
valuation alignment
model alignment
domain validity
input/output artifact binding
exact result binding
```

The exact result is represented by a numerator/denominator equality, avoiding trusted floating-point division. The controlled valid application computes `3/4`.

A second application names the same formula and the same algebraically correct `3/4` result, but its current-risk input becomes available after the decision. Lean proves that the application is invalid. Therefore:

```text
Formula Correct
⇏ Application Correct
```

## Executable contract checker

`tools/formula_contract/` verifies the same obligations over canonical JSON using Python's exact `Fraction` arithmetic. A certificate is emitted only when every gate passes.

The controlled corpus contains nine applications:

- one complete valid application;
- a future input;
- a USD/EUR risk-unit mismatch;
- a risk-model version mismatch;
- a zero hedge-risk denominator;
- a relabeled result;
- a formula-expression hash mismatch;
- a decision before formula registration;
- an output generated after the decision.

Only one application is certified. Five invalid cases have both a matching formula definition and a numerically correct result, demonstrating why formula ID and output equality alone are insufficient.

## General formula certificate

A production formula receipt should bind:

```text
formulaId
expressionHash
implementationHash
registeredAt
input artifact hashes
output artifact hash
unit signature
time and availability semantics
model and calibration version
domain preconditions
numerical tolerance or approximation bound
parent certificate hashes
```

Formula contracts compose with Temporal Noninterference and the Certificate Composition Law. Local data, formula, decision, execution, and result certificates become one global claim only when their object identities and causal boundaries are bridged.

## Assurance boundary

The current module proves one exact hedge-scale contract and provides a reusable application pattern. It does not prove the economic appropriateness of the hedge, the correctness of an external risk model, the truth of input data, or the completeness of the unit vocabulary. Those remain separate certificates and empirical obligations.
