# Proof-Carrying Financial Formula Contracts

A mathematically correct formula can still be applied incorrectly. Financial calculation validity therefore has at least two layers:

```text
formula definition correctness
application correctness at one causal boundary
```

For a hedge scaling formula:

```text
scale = -(currentRisk / hedgeRisk) × riskPercentage / 100
```

the formula text alone does not establish that:

- both risk values were available by the decision time;
- the risks have compatible units and currency;
- the values use the same valuation time;
- the values use the same risk-model version;
- the hedge denominator is nonzero;
- the input artifacts are the exact objects consumed;
- the reported result belongs to those exact inputs and implementation.

## Lean contract

`LeanFinance/Formula/Contract.lean` separates a registered `FormulaDefinition` from one `HedgeScaleApplication`. A valid application carries proofs of:

```text
definition hash match
input availability
nonfuture valuation timestamps
unit compatibility
valuation alignment
model alignment
domain validity
artifact binding
result binding
```

The exact result is represented by a numerator/denominator equality, avoiding trusted floating-point division. The controlled valid application computes `3/4`.

A second controlled application uses the same formula and the same algebraically correct `3/4` result, but its current-risk input becomes available after the decision. Lean proves that this application is invalid. Therefore:

```text
Formula Correct
⇏ Application Correct
```

## Executable contract checker

`tools/formula_contract/` verifies the same obligations over canonical JSON. It uses Python's exact `Fraction` arithmetic and emits a certificate only when every gate passes.

The controlled corpus contains:

- one valid hedge-scale application;
- a future input;
- a USD/EUR risk-unit mismatch;
- a risk-model version mismatch;
- a zero hedge-risk denominator;
- a relabeled result;
- a formula-expression hash mismatch.

Several invalid cases have both a matching formula definition and a numerically correct result. They demonstrate why comparing only the final number or formula ID is insufficient.

## General formula certificate

A production formula receipt should bind:

```text
formulaId
expressionHash
implementationHash
input artifact hashes
output artifact hash
unit signature
time and availability semantics
model and calibration version
domain preconditions
numerical tolerance or approximation bound
parent certificate hashes
```

Formula contracts compose naturally with the repository's Certificate Composition Law. Local data, formula, decision, execution, and result certificates become one global claim only when their object identities and causal boundaries are bridged.

## Assurance boundary

The current module proves one exact hedge-scale contract and provides a reusable application pattern. It does not prove the economic appropriateness of the hedge, the correctness of an external risk model, the truth of input data, or the completeness of the unit vocabulary. Those remain separate certificates and empirical obligations.
