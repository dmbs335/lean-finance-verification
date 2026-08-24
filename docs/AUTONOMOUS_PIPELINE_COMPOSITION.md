# Autonomous Pipeline Certificate Composition

A safe autonomous system cannot rely on a collection of unrelated green reports. The global claim requires one causal chain:

```text
dataset
→ state estimate
→ candidate policy + state
→ shielded decision
→ authorization
→ execution
→ reconciliation
```

Every local artifact may be valid while one boundary refers to another object. The controlled worlds independently substitute the dataset, state, policy, authorization, execution, or reconciliation while preserving all seven local validity flags.

## Binding obligations

The composed claim requires six digest equalities:

- dataset digest appears in the state artifact;
- state and policy digests appear in the decision artifact;
- decision digest appears in authorization;
- authorization digest appears in execution;
- execution digest appears in reconciliation.

Lean proves that five narrow receipt classes jointly verify the controlled global claim and constructs a local-summary counterexample.

## Exact synthesis

The candidate language contains seven channels. `decisionInputBindingReceipt` covers both state→decision and policy→decision, so the exact minimum is:

```text
datasetStateBindingReceipt                 cost 1
decisionInputBindingReceipt                cost 2
decisionAuthorizationBindingReceipt        cost 1
authorizationExecutionBindingReceipt       cost 1
executionReconciliationBindingReceipt      cost 1
                                                     total 6
```

One global autonomous bundle also verifies at cost 9. Every architecture below cost 6 carries an explicit true/false world pair that it cannot distinguish.

## Assurance boundary

Artifact digests and local-validity claims are controlled inputs. The receipts are not independently authenticated, the substitution language is finite, and no broker or market statement is made. This layer specifies the causal composition contract that a production runtime must satisfy.
