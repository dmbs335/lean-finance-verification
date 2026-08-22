# Epistemic Connectivity

Ordinary evidence separation asks whether every claim-disagreement history pair has at
least one selected separator. Epistemic connectivity asks whether that remains true
after declared evidence failures.

For a failure scenario `f`, let `S_f` be the selected channels that survive. The
repository defines:

```text
failure-robust verification
  every S_f verifies the claim

failure connectivity
  after every f, every claim-disagreement pair has
  a surviving selected separator
```

Lean proves the exact duality:

```lean
FailureRobustVerifies ↔ FailureConnectivity
```

This is the fault-tolerant extension of evidence cut-set duality.

## Monotonicity

Two structural laws follow:

- selecting more channels cannot reduce robustness;
- surviving more channels under each failure cannot reduce robustness.

A bounded executable form filters a selected channel list for each declared scenario,
checks the complete finite history catalog, and lifts each successful check to the
semantic channel-verification contract.

## Channel failures versus trust-domain failures

A single channel failure removes one evidence source. A trust-domain failure removes
every source controlled by a common provider, credential boundary, host, CA, cloud
account, or operational authority.

The distinction matters:

```text
two receipts
≠
two independent evidence boundaries
```

If two receipts share one compromise domain, one domain failure removes both.
`survivesDomainFailure` models this correlated failure directly.

## Cost-model-tampering result

The exact minimum-cost evidence design has cost 8 and contains one cost-model mutation
separator. Removing `targetedReceipt_tamperCostModel` makes the honest execution and
observed control-plane attack indistinguishable. Thus the cost optimum has epistemic
connectivity one but zero tolerance for channel failure.

A redundant design adds:

```text
backup declaration receipt
full executor audit
backup cost-model-tampering receipt
```

Together with the three targeted receipts and the primary self-report, every primitive
integrity boundary has two removable separator paths. Lean exhaustively checks the 32
history model and proves the design survives every one of eight declared single-channel
failure scenarios.

The selected robust design costs 20 in the current policy model. This exposes a new
trade-off:

```text
minimum exact verification cost: 8
minimum demonstrated one-channel-resilient architecture: 20
```

The current PR does not yet prove 20 is the global robust minimum; it proves the
architecture is robust and gives a mechanically checked upper bound.

## Trust-domain result

With independent domains:

- primary and backup declarations are separate;
- targeted execution receipts and the full executor audit are separate;
- primary and backup control-plane receipts are separate.

Lean proves the same architecture survives any single declared domain outage.

When the duplicate declaration and tamper receipts are reassigned to the same domains,
Lean constructs the control-domain counterexample. One domain failure removes both
tamper separators, restoring observational equivalence between the honest and
cost-model-tampering histories.

Therefore resilience is governed by separator-domain diversity, not evidence item
count.

## Next step

The next synthesis problem is:

```text
minimize evidence cost
subject to failure connectivity under a declared fault family
```

That produces a cost–resilience frontier rather than one minimum-cost verification
point. Multi-provider timestamp quorum, independent execution receipts, and
transparency logs then become concrete instances of the same robust separation theory.
