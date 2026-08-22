# Evidence-Obligation Taxonomy

Attack names describe mechanism. Evidence-obligation signatures describe what must be
observed to distinguish the attack from a trusted reference history.

For reference history `h` and attack history `a`, define:

```text
Σ_h(a) = { channel | observe(channel, h) ≠ observe(channel, a) }
```

Two attacks are epistemically equivalent when their signatures are equal. This is a
different classification from exploit technique, event order, or affected component.

## Formal relations

`EvidenceTaxonomy.lean` defines:

- exact separator-signature equivalence;
- separator-signature inclusion;
- basis novelty, where the current selected evidence detects no distinction;
- exact class novelty relative to a known attack catalog;
- unseen-separator novelty;
- strong new-observation-boundary novelty.

Signature equivalence is proved reflexive, symmetric, and transitive. It transfers
detection and basis novelty across any selected evidence list.

Signature inclusion has an operational interpretation:

```text
Σ(source) ⊆ Σ(target)
```

means every basis that detects `source` also detects `target`. A smaller signature is a
stricter evidence obligation because fewer channels can satisfy it.

## Primitive signatures in the refined backtest workflow

Relative to the honest declared baseline:

```text
undeclared baseline
  { selfReport }

hidden parameter sweep
  { fullExecutorLog, targetedReceipt_executeHiddenSweep }

future-data access
  { fullExecutorLog, targetedReceipt_readFutureData }

cost-model tampering
  { targetedReceipt_tamperCostModel }

hidden + future composite
  { fullExecutorLog,
    targetedReceipt_executeHiddenSweep,
    targetedReceipt_readFutureData }
```

The cost-model mutation is especially strong: it has a unique separator and is invisible
to the result bundle, RFC 3161 anchor, full executor log, and every prior targeted
receipt.

## Equivalence versus syntax

`dualAttack` and `history16` execute hidden-sweep and future-data actions in different
orders. Lean proves they are distinct histories but have the same separator signature.
They therefore belong to one epistemic attack class.

This shows why trace strings alone are the wrong taxonomy: syntactically different
attacks may require exactly the same evidence architecture.

## Novelty result

The pre-tampering catalog contains:

```text
undeclaredBaseline
hiddenSweep
futureLeak
dualAttack
```

Its exact minimum basis is:

```text
selfReport
hidden-sweep receipt
future-data receipt
```

The observed `costModelTampering` trace is proved to:

1. have no exact signature match in the known catalog;
2. be undetectable by the old basis;
3. introduce a separator channel unused by every known attack.

It is therefore a mechanically certified **new observation boundary**, rather than
merely another attack instance. Adding the targeted cost-model receipt closes the new
obligation.

## Automated report

`tools/evidence_taxonomy` reads a canonical evidence model and emits:

- each attack's separator signature;
- exact epistemic equivalence classes;
- strict signature-subsumption relations;
- candidate novelty relative to a declared known catalog;
- current-basis coverage;
- unseen separator channels;
- a deterministic novelty classification.

The checked fixture classifies `history16` as an existing class represented by
`dualAttack`, while classifying `costModelTampering` as `new_observation_boundary`.

## Research use

A large attack corpus can now be evaluated by questions that scale better than attack
names:

```text
How many distinct evidence-obligation classes exist?
Which attacks introduce genuinely new observation boundaries?
Which classes have unique separators?
Which classes share one broad but privacy-heavy channel?
How much marginal evidence debt does each novel class add?
```

The intended contribution is not another vulnerability taxonomy. It is a taxonomy of
the observation obligations required to make research-integrity claims verifiable.
