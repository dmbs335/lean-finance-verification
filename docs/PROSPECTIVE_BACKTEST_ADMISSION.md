# Prospective Backtest Admission

Exact replay of an old backtest establishes reproducibility but cannot retroactively establish preregistration or eliminate hidden search. This module defines the separate contract required for a future untouched-window result to become research-admissible.

## Structural gates before outcomes

A plan must be registered before its first decision and before the untouched outcome window. It binds:

```text
code
parameters
metric
benchmark
cost model
point-in-time universe
primary trial
complete registered trial set
minimum result lower bound
```

Execution must use exactly those digests, select the preregistered primary trial, disclose every executed trial, and have the exact registered trial set. Any extra hidden trial or post-hoc cost-model change rejects the package.

## Outcome states

A structurally valid plan with no outcome is `pending`; this is not a failed experiment. Once an outcome is presented, it must cover the exact registered window and be available only after that window ends. A premature or wrong-window outcome is rejected rather than treated as pending.

A mature outcome is admitted only when strict point-in-time verification passes and the primary result lower bound clears the preregistered threshold.

The controlled package is admitted with result LCB 5 bps over a threshold of 3 bps. Counterfactual tests reject post-hoc registration, hidden trials, cost-model mutation, premature outcome presentation, failed strict-PIT, and a lower bound of 2 bps.

## Assurance boundary

Digest authenticity and the strict-PIT verifier remain external. The registered trial language may still omit real human discretion. `admitted-controlled` means the finite admission contract passed; it is not an investment recommendation, future-profit guarantee, or order authorization.
