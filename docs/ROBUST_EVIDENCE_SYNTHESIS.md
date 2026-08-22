# Exact Robust Evidence Synthesis

Epistemic connectivity characterizes whether a selected evidence architecture survives
a declared failure family. Exact robust synthesis adds optimization:

```text
minimize evidence cost
subject to every declared failure retaining a separator
for every claim-disagreement history pair
```

`RobustSynthesis.lean` defines a finite Boolean checker over an explicit failure list,
proves it sound and complete for bounded robust verification, and packages an exact
minimum as a proof-carrying `RobustEvidenceDebtCertificate`.

## Complete candidate language

The cost-model-tampering model has nine available channels after adding independent
backup declaration and control-plane receipts. Candidate selections are represented by
`Fin 512`, so every one of the `2^9` subsets is checked.

Two complete failure families are analyzed:

```text
single-channel family
  no failure + loss of each one of nine channels

single-domain family
  no failure + outage of each one of seven independent trust domains
```

Lean checks every candidate against all 32 bounded terminal histories after every
scenario.

## Exact result

The minimum robust architecture is:

```text
selfReport
backupDeclaration
targetedReceipt_executeHiddenSweep
targetedReceipt_readFutureData
fullExecutorLog
targetedReceipt_tamperCostModel
backupTamperReceipt
```

Its cost is 20. It is minimum under both:

- arbitrary loss of one selected channel;
- outage of one declared independent trust domain.

The non-resilient exact optimum costs 8, so the exact single-failure resilience premium
is 12 cost units in the current policy model.

## Why the seven channels are necessary

The bounded attack model contains four primitive evidence obligations:

```text
undeclared baseline
  primary + backup declaration paths

hidden sweep
  targeted hidden-sweep receipt + full executor audit

future-data access
  targeted future-data receipt + full executor audit

cost-model mutation
  primary + backup control-plane receipts
```

The full executor audit is shared by the two execution/data-access obligations. Result
bundles and RFC 3161 timestamps do not separate any of these upstream hidden actions,
so adding them cannot reduce robust cost for this claim.

## Trust-domain interpretation

Two evidence items only create two robust paths when their compromise domains are
independent. The domain checker removes all channels in one domain at once. This makes
multi-provider timestamps, independent execution receipts, and transparency logs
instances of the same optimization problem rather than special-purpose quorum rules.

## Boundary

The optimum is exact for:

- the 32-history bounded workflow;
- the nine declared channels;
- the ten channel-failure scenarios;
- the eight domain-failure scenarios;
- the declared scalar costs and trust-domain assignments.

It does not establish independence of real providers or completeness of the attack and
failure models. Those remain external modeling obligations.
