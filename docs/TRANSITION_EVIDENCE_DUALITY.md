# Transition-Level Safety–Observability Duality

History-level evidence separation compares every pair of complete research histories on
which a claim changes truth value. Exact, but potentially redundant: many terminal
attacks share the same first claim-changing transition.

`TransitionSeparation.lean` introduces a complete first-violation classifier:

```text
history → none                 safe history
history → some violation-kind  first claim-changing transition
```

The transition pair-cover condition requires a selected separator between every safe
history and every history in each first-violation class. Lean proves the exact duality:

```text
first-violation pair cover
↔
verification of first-violation absence
```

Grouping histories by first violation therefore loses no information relative to the
classifier.

## Persistent transition receipts

A stronger, implementable sufficient condition assigns one selected receipt to each
occurring violation kind. The receipt must distinguish every terminal history in that
class from every safe history. This combines:

- **specificity** — safe histories do not produce the violating receipt;
- **persistence** — later workflow actions do not erase the distinction.

Lean proves:

```text
persistent cover
→ pair cover
→ verification
```

## Silent first-violation impossibility

A `SilentFirstViolationWitness` contains:

- one safe history;
- one bad history and its first-violation kind;
- equality on every selected evidence channel.

The theorem

```lean
silent_first_violation_implies_unverifiable
```

shows that no selected family with such a witness verifies violation absence.

## Cost-model-tampering result

The refined workflow has 32 terminal histories: one safe and 31 violating. The first
violation classifier compresses those 31 terminal disagreement pairs into four
primitive obligations:

```text
undeclared execution
hidden parameter sweep
future-data access
cost-model mutation
```

The persistent receipt cover is:

```text
selfReport
targetedReceipt_executeHiddenSweep
targetedReceipt_readFutureData
targetedReceipt_tamperCostModel
```

This equals the exact history-level minimum-cost basis. Lean proves each receipt is
persistent across every terminal continuation in its class, and proves the basis
verifies the original generated integrity claim.

The publication-side declaration/result/timestamp family remains silent on the
cost-model first violation and therefore cannot verify the claim.

## Computational consequence

The current example reduces 31 terminal disagreement obligations to four transition
obligations while preserving the same minimum evidence architecture. For larger
workflows, transition obligations can be generated from reachable safe-to-unsafe state
action edges instead of enumerating every terminal continuation pair.

The persistent-cover condition is stronger than arbitrary history-pair verification:
it asks for one receipt that works uniformly for an entire transition class. When such
receipts exist, they provide a compact and operational evidence design.

## Boundary

The classifier must be complete: `none` must correspond exactly to the claim being
true. Persistence is evaluated over the declared bounded workflow. A later action that
can erase or forge a receipt invalidates the persistent-separator assumption and must
be modeled explicitly.
